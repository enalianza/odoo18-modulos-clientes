from odoo import models, fields, api
from datetime import datetime, timedelta
from odoo.exceptions import UserError
from datetime import datetime, timedelta
# Este es el de Histórico de cálculos

class MinMaxCalculation(models.Model):
    _name = 'minmax.calculation'
    _description = 'Cálculo de Mínimos y Máximos'
    _rec_name = 'calculation_date'
    _order = 'calculation_date desc'

    calculation_date = fields.Datetime(string='Fecha de cálculo',
                                      default=fields.Datetime.now, readonly=True)
    user_id = fields.Many2one('res.users', string='Usuario',
                             default=lambda self: self.env.user, readonly=True)
    warehouse_ids = fields.Many2many('stock.warehouse',
                                    string='Almacenes')
    min_coverage_days = fields.Integer(string='Cobertura mínima (días)',
                                    help='Cobertura estimada de ventas mínimas en estos días',
                                    default=60)
    max_coverage_days = fields.Integer(string='Cobertura máxima (días)',
                                    help='Cobertura estimada de ventas máximas en estos días',
                                    default=90)
    include_inactive = fields.Boolean(string='Incluir productos inactivos', 
                                    default=False)
    
    # Mantener este campo para compatibilidad, pero ya no se utilizará directamente
    product_ids = fields.Many2many(
        'product.product',
        string='Productos específicos',
        domain=[('type', 'in', ['product', 'consu'])]
    )
    
    # Nuevo campo para las líneas de productos
    product_line_ids = fields.One2many(
        'minmax.product.line',
        'calculation_id',
        string='Productos específicos'
    )
    
    product_category_ids = fields.Many2many(
        'product.category',
        string='Categorías de productos'
    )
    
    round_to_multiple = fields.Boolean(string='Redondear a múltiplos de compra',
                        help='Redondeará hacia las unidades que que sean multiplos de sus unidades de compra',
                        default=True)
    
    date_start = fields.Date(string='Fecha inicial de análisis', 
                        default=lambda self: fields.Date.today() - timedelta(days=365),
                        help='Fecha inicial de análisis del periodo de ventas',
                        required=True)
    date_end = fields.Date(string='Fecha final de análisis', 
                        default=lambda self: fields.Date.today(),
                        help='Fecha final de análisis del periodo de ventas',
                        required=True)
    adjustment_factor = fields.Float(string='Factor de ajuste (%)', 
                        default=20.0,
                        help='Porcentaje para ajustar la demanda según estacionalidad o tendencias',
                        required=True)

    # Cambiando a line_ids por consistencia
    line_ids = fields.One2many('minmax.calculation.line',
                              'calculation_id', string='Líneas de cálculo')
    
    state = fields.Selection([
        ('draft', 'Borrador'),
        ('calculated', 'Calculado'),
        ('applied', 'Aplicado')
    ], string='Estado', default='draft')

    @api.model_create_multi
    def create(self, vals_list):
        records = super(MinMaxCalculation, self).create(vals_list)
        return records

    def _generate_calculation_lines(self):
        self.ensure_one()

        # Eliminar líneas existentes si las hay
        self.line_ids.unlink()

        # Lista para almacenar productos
        products = self.env['product.product']
        
        # Obtener productos de las líneas específicas
        specific_products = self.product_line_ids.mapped('product_id')
        products |= specific_products
        
        # Si hay categorías seleccionadas, incluir esos productos
        if self.product_category_ids:
            domain = [
                ('type', 'in', ['product', 'consu']),
                ('categ_id', 'child_of', self.product_category_ids.ids)
            ]
            
            # Si no incluir inactivos
            if not self.include_inactive:
                domain.append(('active', '=', True))
                
            category_products = self.env['product.product'].search(domain)
            products |= category_products
        
        # Mantener compatibilidad con el campo antiguo product_ids (por si hay datos existentes)
        if self.product_ids:
            products |= self.product_ids
        
        # Eliminar duplicados
        products = products.filtered(lambda p: p.id)
        
        if not products:
            return False

        line_vals = []
        for warehouse in self.warehouse_ids:
            for product in products:
                # Buscar regla de reabastecimiento existente
                orderpoint = self.env['stock.warehouse.orderpoint'].search([
                    ('warehouse_id', '=', warehouse.id),
                    ('product_id', '=', product.id),
                    ('active', '=', True)
                ], limit=1)

                # Obtener datos del proveedor principal
                seller = product.seller_ids and product.seller_ids[0] or False
                lead_time = seller and seller.delay or 0
                qty_multiple = seller and seller.min_qty or 1.0

                vals = {
                    'calculation_id': self.id,
                    'product_id': product.id,
                    'warehouse_id': warehouse.id,
                    'current_min': orderpoint and orderpoint.product_min_qty or 0.0,
                    'current_max': orderpoint and orderpoint.product_max_qty or 0.0,
                    'lead_time_days': lead_time,
                    'qty_multiple': qty_multiple,
                    'orderpoint_id': orderpoint and orderpoint.id or False,
                    'suggested_min': 0.0,
                    'suggested_max': 0.0,
                }
                line_vals.append(vals)

        # Crear las líneas
        if line_vals:
            self.env['minmax.calculation.line'].create(line_vals)
            return True
            
        return False

    def action_calculate(self):
        self.ensure_one()
        
        # Generar las líneas de cálculo
        if not self._generate_calculation_lines():
            raise UserError('No se encontraron productos para el cálculo')
        
        if not self.line_ids:
            raise UserError('No hay líneas para calcular')
        
        # Comprobar qué módulos están instalados
        sale_installed = self.env['ir.module.module'].sudo().search([
            ('name', '=', 'sale'),
            ('state', '=', 'installed'),
        ], limit=1)
        
        pos_installed = self.env['ir.module.module'].sudo().search([
            ('name', '=', 'point_of_sale'),
            ('state', '=', 'installed'),
        ], limit=1)
        
        if not sale_installed and not pos_installed:
            raise UserError('Para usar este módulo, debe tener instalado al menos el módulo de Ventas o el de Punto de Venta.')
        
        # Usar el período de análisis definido por el usuario
        date_start = self.date_start
        date_end = self.date_end
        
        for line in self.line_ids:
            product = line.product_id
            warehouse = line.warehouse_id
            total_qty = 0.0
            
            # 1. Analizar órdenes de venta confirmadas y entregadas (si el módulo está instalado)
            if sale_installed:
                sale_domain = [
                    ('state', '=', 'sale'),  # Órdenes confirmadas
                    ('order_line.product_id', '=', product.id),
                    ('date_order', '>=', date_start),
                    ('date_order', '<=', date_end),
                    ('warehouse_id', '=', warehouse.id)
                ]
                
                sales = self.env['sale.order'].search(sale_domain)
                
                # Filtrar por líneas entregadas completamente
                for sale in sales:
                    for sale_line in sale.order_line.filtered(lambda l: l.product_id.id == product.id):
                        # Verificar si está completamente entregada
                        if sale_line.qty_delivered >= sale_line.product_uom_qty:
                            total_qty += sale_line.product_uom_qty
            
            # 2. Analizar pedidos de POS cerrados (si el módulo está instalado)
            if pos_installed:
                pos_domain = [
                    ('state', '=', 'done'),  # Pedidos pagados y procesados
                    ('lines.product_id', '=', product.id),
                    ('date_order', '>=', date_start),
                    ('date_order', '<=', date_end)
                ]
                
                # El almacén en POS se determina por config_id
                pos_configs = self.env['pos.config'].search([('warehouse_id', '=', warehouse.id)])
                if pos_configs:
                    pos_domain.append(('config_id', 'in', pos_configs.ids))
                
                pos_orders = self.env['pos.order'].search(pos_domain)
                
                for pos_order in pos_orders:
                    for pos_line in pos_order.lines.filtered(lambda l: l.product_id.id == product.id):
                        total_qty += pos_line.qty
            
            # Si no hay datos de ventas, podemos usar movimientos de stock como fallback
            if total_qty == 0:
                domain = [
                    ('state', '=', 'done'),
                    ('product_id', '=', product.id),
                    ('date', '>=', date_start),
                    ('date', '<=', date_end),
                    ('location_dest_id.usage', '=', 'customer'),  # Solo movimientos a clientes
                ]
                
                if warehouse:
                    domain.append(('picking_id.picking_type_id.warehouse_id', '=', warehouse.id))
                
                # Obtener movimientos de stock de salida
                moves = self.env['stock.move'].search(domain)
                total_qty = sum(moves.mapped('product_qty'))
            
            # Calcular la demanda diaria estimada
            days = (date_end - date_start).days + 1  # +1 para incluir ambos días
            avg_daily_demand = (total_qty / days) * (1 + self.adjustment_factor / 100.0)
            
            # Guardar las unidades vendidas
            line.total_sold = total_qty
            
            # Guardar la demanda calculada
            line.avg_daily_demand = avg_daily_demand
            
            # Calcular mínimos y máximos
            min_qty = avg_daily_demand * (line.lead_time_days + self.min_coverage_days)
            max_qty = avg_daily_demand * (line.lead_time_days + self.max_coverage_days)
            
            # Redondear a múltiplos de compra si es necesario
            if self.round_to_multiple and line.qty_multiple > 0:
                if min_qty > 0:
                    min_qty = (min_qty // line.qty_multiple) * line.qty_multiple
                    if min_qty < avg_daily_demand * line.lead_time_days:
                        min_qty += line.qty_multiple
                
                if max_qty > 0:
                    max_qty = (max_qty // line.qty_multiple) * line.qty_multiple
                    if max_qty < min_qty:
                        max_qty += line.qty_multiple
            
            line.suggested_min = min_qty
            line.suggested_max = max_qty
        
        self.state = 'calculated'
        return True

    def action_apply(self):
        self.ensure_one()
        
        if self.state != 'calculated':
            return True

        OrderPoint = self.env['stock.warehouse.orderpoint']
        
        for line in self.line_ids.filtered(lambda l: l.apply if hasattr(l, 'apply') else True):
            # Valores para el orderpoint
            orderpoint_vals = {
                'product_id': line.product_id.id,
                'warehouse_id': line.warehouse_id.id,
                'product_min_qty': line.suggested_min,
                'product_max_qty': line.suggested_max,
                'qty_multiple': line.qty_multiple,
            }

            # Si ya existe un orderpoint, actualizarlo
            if line.orderpoint_id:
                line.orderpoint_id.write(orderpoint_vals)
            # Si no existe, crearlo
            else:
                # Añadir valores adicionales necesarios para crear
                orderpoint_vals.update({
                    'name': f'{line.product_id.name} - {line.warehouse_id.name}',
                    'location_id': line.warehouse_id.lot_stock_id.id,
                })
                orderpoint = OrderPoint.create(orderpoint_vals)
                line.orderpoint_id = orderpoint.id

        self.state = 'applied'
        return True
    