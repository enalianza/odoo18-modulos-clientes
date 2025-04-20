from odoo import models, fields, api
from odoo.exceptions import UserError

class MinMaxWizard(models.TransientModel):
    _name = 'minmax.wizard'
    _description = 'Asistente para cálculo de mínimos y máximos'
    
    warehouse_ids = fields.Many2many('stock.warehouse', string='Almacenes', required=True)
    product_ids = fields.Many2many('product.product', string='Productos específicos',
                                  domain=[('type', '=', 'product')])
    product_category_ids = fields.Many2many('product.category', string='Categorías de productos')
    include_inactive = fields.Boolean(string='Incluir productos inactivos', default=False)
    min_coverage_days = fields.Integer(string='Cobertura mínima (días)', default=60, required=True)
    max_coverage_days = fields.Integer(string='Cobertura máxima (días)', default=90, required=True)
    round_to_multiple = fields.Boolean(string='Redondear a múltiplo de compra', default=True)
    
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
        }
        
        calculation = self.env['minmax.calculation'].create(calculation_vals)
        
        # Generar las líneas basadas en los criterios seleccionados
        domain = [('type', '=', 'product')]
        
        if not self.include_inactive:
            domain.append(('active', '=', True))
            
        if self.product_ids:
            domain.append(('id', 'in', self.product_ids.ids))
        elif self.product_category_ids:
            domain.append(('categ_id', 'child_of', self.product_category_ids.ids))
            
        products = self.env['product.product'].search(domain)
        
        calculation._generate_calculation_lines(products)
        calculation.action_calculate()
        
        # Abrir el formulario con los resultados
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'minmax.calculation',
            'res_id': calculation.id,
            'view_mode': 'form',
            'target': 'current',
        }
    