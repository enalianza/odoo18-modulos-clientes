from odoo import models, fields, api

class MinmaxProductLine(models.Model):
    _name = 'minmax.product.line'
    _description = 'Línea de producto para cálculo min/max'

    calculation_id = fields.Many2one('minmax.calculation',
        string='Cálculo', 
        ondelete='cascade')
    
    product_id = fields.Many2one(
        'product.product', 
        string='Producto',
        domain=[('type', '=', 'product')]
    )
    
    name = fields.Char(
        related='product_id.name', 
        string='Nombre'
    )
    
    product_type = fields.Selection(
        related='product_id.type',
        string='Tipo de producto'
    )
    
    qty_available = fields.Float(
        related='product_id.qty_available',
        string='Cantidad a mano'
    )
    