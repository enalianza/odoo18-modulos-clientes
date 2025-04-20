{
    'name': 'Mínimos y Máximos con BI',
    'version': '0.1',
    'category': 'Inventory',
    'summary': 'Optimización de stock usando BI',
    'description': 'Submódulo para sugerir mínimos y máximos con base en datos históricos y análisis.',
    'author': 'enAlianza',
    # no vale la linea 'depends': ['base', 'stock', 'enalianza_suite'],
    'depends': ['stock', 'purchase', 'product', 'enalianza_suite'],
    'data': [
        'security/ir.model.access.csv',
        'views/minmax_menu.xml',
    ],
    'demo': [],
    'installable': True,
    'application': False,
    'auto_install': False,
    'license': 'LGPL-3',
}
