from odoo import models, fields, api

class MinMaxCalculationLine(models.Model):
    _name = 'minmax.calculation.line'
    _description = 'Línea de cálculo de mínimos y máximos'
    
    calculation_id = fields.Many2one('minmax.calculation', string='Cálculo', ondelete='cascade')
    product_id = fields.Many2one('product.product', string='Producto', required=True)
    warehouse_id = fields.Many2one('stock.warehouse', string='Almacén', required=True)
    current_min = fields.Float(string='Mínimo actual', digits='Product Unit of Measure')
    current_max = fields.Float(string='Máximo actual', digits='Product Unit of Measure')
    suggested_min = fields.Float(string='Mínimo sugerido', digits='Product Unit of Measure')
    suggested_max = fields.Float(string='Máximo sugerido', digits='Product Unit of Measure')
    avg_daily_demand = fields.Float(string='Demanda diaria estimada', digits='Product Unit of Measure',
                        help='(Unidades vendidas / Días analizados) × (1 + Factor de ajuste/100)')
    lead_time_days = fields.Integer(string='Plazo de entrega (días)')
    total_sold = fields.Float(string='Vendidos', digits='Product Unit of Measure', 
                         help='Cantidad total vendida y entregada en el período')
    adjustment_factor = fields.Float(string='Factor de ajuste (%)', default=100.0)
    qty_multiple = fields.Float(string='Múltiplo de compra', digits='Product Unit of Measure', default=1.0)
    orderpoint_id = fields.Many2one('stock.warehouse.orderpoint', string='Regla de reabastecimiento')
    apply = fields.Boolean(string='Aplicar', default=True)
    