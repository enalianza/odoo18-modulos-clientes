
from odoo import api, fields, models
from datetime import date

class ReplenishmentOptimizerWizard(models.TransientModel):
    _name = 'stock.replenishment.optimizer.wizard'
    _description = 'Asistente de cálculo de mínimos y máximos con BI'

    date_from = fields.Date(string='Desde', required=True, default=lambda self: date.today().replace(day=1),
                            help='Se analizarán salidas de inventario realizadas desde esta fecha.')
    date_to = fields.Date(string='Hasta', required=True, default=lambda self: date.today(),
                          help='Se analizarán salidas hasta esta fecha (incluida).')
    location_ids = fields.Many2many('stock.location', string='Almacenes',
                                    help='Seleccione uno o varios almacenes desde los cuales se realizarán los cálculos.')
    categ_ids = fields.Many2many('product.category', string='Categorías de producto',
                                 help='Todos los productos activos y almacenables de estas categorías serán incluidos en el análisis.')
    product_ids = fields.Many2many('product.product', string='Productos específicos',
                                   help='Puede seleccionar productos puntuales para limitar el cálculo.')
    coverage_days = fields.Integer(string='Horizonte de planificación (días)', default=60, required=True,
                                   help='Cantidad de días futuros que se desea cubrir con inventario, además del tiempo de entrega del proveedor.')
    adjustment_factor = fields.Float(string='Factor de ajuste (%)', default=0.0,
                                     help='Permite aumentar o disminuir la demanda estimada según eventos futuros (promociones, estacionalidad, etc.).')
    exclude_inactive = fields.Boolean(string='Excluir productos inactivos', default=True,
                                      help='Si está activado, se excluirán del análisis los productos que estén archivados o dados de baja.')
    round_to_multiple = fields.Boolean(string='Redondear a múltiplos de compra', default=True,
                                       help='Si está activado, los valores sugeridos se ajustarán automáticamente al múltiplo de compra del proveedor principal.')

    def action_calculate(self):
        # Esta función se completará en el desarrollo técnico.
        return {'type': 'ir.actions.act_window_close'}
