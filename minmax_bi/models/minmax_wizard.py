from odoo import models, fields, api
from odoo.exceptions import UserError

class MinMaxWizard(models.TransientModel):
    _name = 'minmax.wizard'
    _description = 'Asistente para cálculo de mínimos y máximos'

    warehouse_ids = fields.Many2many('stock.warehouse', string='Almacenes', required=True)
    
    # Mantenemos este campo para compatibilidad, pero ya no se mostrará en la vista
    product_ids = fields.Many2many(
        'product.product', 
        string='Productos específicos',
        domain=[('type', '=', 'product', 'consu')]
    )
    
    # Nuevo campo para las líneas de productos
    product_line_ids = fields.One2many(
        'minmax.wizard.product.line',
        'wizard_id',
        string='Productos específicos'
    )
    
    product_category_ids = fields.Many2many(
        'product.category', 
        string='Categorías de productos'
    )
    
    include_inactive = fields.Boolean(
        string='Incluir productos inactivos', 
        default=False
    )
    
    min_coverage_days = fields.Integer(
        string='Cobertura mínima (días)', 
        default=60, 
        required=True
    )
    
    max_coverage_days = fields.Integer(
        string='Cobertura máxima (días)', 
        default=90, 
        required=True
    )
    
    round_to_multiple = fields.Boolean(
        string='Redondear a múltiplo de compra', 
        default=True
    )

    @api.constrains('min_coverage_days', 'max_coverage_days')
    def _check_coverage_days(self):
        for record in self:
            if record.min_coverage_days >= record.max_coverage_days:
                raise UserError('La cobertura mínima debe ser menor que la máxima')

    def action_calculate(self):
        self.ensure_one()

        # Crear el registro de cálculo
        calculation_vals = {
            'warehouse_ids': [(6, 0, self.warehouse_ids.ids)],
            'min_coverage_days': self.min_coverage_days,
            'max_coverage_days': self.max_coverage_days,
            'include_inactive': self.include_inactive,
            'round_to_multiple': self.round_to_multiple,
            # Mantener compatibilidad con el campo product_ids
            'product_ids': [(6, 0, self.product_ids.ids)],
            'product_category_ids': [(6, 0, self.product_category_ids.ids)],
        }
        
        # Crear el cálculo
        calculation = self.env['minmax.calculation'].create(calculation_vals)
        
        # Transferir las líneas de productos específicos si existen
        if self.product_line_ids:
            for line in self.product_line_ids:
                self.env['minmax.product.line'].create({
                    'calculation_id': calculation.id,
                    'product_id': line.product_id.id,
                })
        
        # Llamar al método calculate para generar y calcular las líneas
        calculation.action_calculate()

        # Abrir el formulario con los resultados
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'minmax.calculation',
            'res_id': calculation.id,
            'view_mode': 'form',
            'target': 'current',
        }


class MinmaxWizardProductLine(models.TransientModel):
    _name = 'minmax.wizard.product.line'
    _description = 'Línea de producto para asistente de cálculo min/max'

    wizard_id = fields.Many2one(
        'minmax.wizard',
        string='Asistente',
        ondelete='cascade'
    )
    
    product_id = fields.Many2one(
        'product.product', 
        string='Producto',
        domain=[('type', '=', 'product', 'consu')]
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
    