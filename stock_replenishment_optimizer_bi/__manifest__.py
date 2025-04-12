# -*- coding: utf-8 -*-
{
    'name': 'Mínimos y Máximos con BI',
    'version': '1.0',
    'summary': 'Cálculo automático de mínimos y máximos por producto y almacén basado en salidas reales',
    'description': 'Este módulo permite calcular de forma inteligente los niveles de inventario mínimos y máximos sugeridos por producto y almacén, considerando salidas reales, lead time del proveedor, horizonte de planeación y ajustes manuales.',
    'category': 'Inventory',
    'author': 'enAlianza / Consultoría Odoo',
    'depends': ['stock', 'sale', 'purchase', 'point_of_sale'],
    'data': [
        'security/ir.model.access.csv',
        'views/menu.xml',
        'views/replenishment_wizard_view.xml',
    ],
    'installable': True,
    'application': False,
    'license': 'OEEL-1',
}
