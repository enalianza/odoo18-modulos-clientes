from odoo import models, fields, api
from datetime import datetime, timedelta
from odoo.exceptions import UserError

class MinMaxCalculation(models.Model):
    _name = 'minmax.calculation'
    _description = 'Cálculo de Mínimos y Máximos'
    _rec_name = 'calculation_date'
    _order = 'calculation_date desc'
    
    calculation_date = fields.Datetime(string='Fecha de cálculo', default=fields.Datetime.now, readonly=True)
    user_id = fields.Many2one('res.users', string='Usuario', default=lambda self: self.env.user, readonly=True)
    warehouse_ids = fields.Many2many('stock.warehouse', string='Almacenes')
    min_coverage_days = fields.Integer(string='Cobertura mínima (días)', default=60)
    max_coverage_days = fields.Integer(string='Cobertura máxima (días)', default=90)
    include_inactive = fields.Boolean(string='Incluir productos inactivos', default=False)
    round_to_multiple = fields.Boolean(string='Redondear a múltiplo de compra', default=True)
    line_ids = fields.One2many('minmax.calculation.line', 'calculation_id', string='Líneas de cálculo')
    state = fields.Selection([
        ('draft', 'Borrador'),
        ('calculated', 'Calculado'),
        ('applied', 'Aplicado')
    ], string='Estado', default='draft')
    
    @api.model_create_multi
    def create(self, vals_list):
        records = super(MinMaxCalculation, self).create(vals_list)
        return records
        
    def _generate_calculation_lines(self, products):
        self.ensure_one()
        
        # Eliminar líneas existentes si las hay
        self.line_ids.unlink()
        
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
        self.env['minmax.calculation.line'].create(line_vals)
        
    def action_calculate(self):
        self.ensure_one()
        
        if not self.line_ids:
            raise UserError('No hay líneas para calcular')
        
        # Período de análisis: un año hacia atrás para capturar estacionalidad
        date_end = fields.Date.today()
        date_start = date_end - timedelta(days=365)
        
        for line in self.line_ids:
            # Obtener las ventas del período
            domain = [
                ('state', '=', 'done'),
                ('product_id', '=', line.product_id.id),
                ('date', '>=', date_start),
                ('date', '<=', date_end),
            ]
            
            if line.warehouse_id:
                domain.append(('picking_id.picking_type_id.warehouse_id', '=', line.warehouse_id.id))
            
            # Obtener movimientos de stock de salida
            moves = self.env['stock.move'].search(domain)
            
            # Calcular la demanda diaria promedio
            total_qty = sum(moves.mapped('product_qty'))
            days = (date_end - date_start).days or 1
            avg_daily_demand = total_qty / days
            
            # Aplicar factor de ajuste (por defecto 100%)
            avg_daily_demand = avg_daily_demand * (line.adjustment_factor / 100.0)
            
            # Guardar la demanda calculada
            line.avg_daily_demand = avg_daily_demand
            
            # Calcular mínimos y máximos
            min_qty = avg_daily_demand * (line.lead_time_days + self.min_coverage_days)
            max_qty = avg_daily_demand * (line.lead_time_days + self.max_coverage_days)
            
            # Redondear a múltiplos de compra si es necesario
            if self.round_to_multiple and line.qty_multiple > 0:
                min_qty = (min_qty // line.qty_multiple) * line.qty_multiple
                if min_qty < avg_daily_demand * line.lead_time_days:
                    min_qty += line.qty_multiple
                    
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
        
        for line in self.line_ids.filtered(lambda l: l.apply):
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
    