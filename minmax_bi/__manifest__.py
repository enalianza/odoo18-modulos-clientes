{
    'name': 'Mínimos y Máximos con BI',
    'version': '0.1',
    'category': 'Inventory',
    'summary': 'Optimización de stock usando BI',
    'description': 'Submódulo para sugerir mínimos y máximos con base en datos históricos y análisis.',
    'author': 'enAlianza',
    'depends': ['base', 'stock', 'enalianza_suite'],  # stock porque estará dentro de Inventario
    'data': [
        'views/minmax_menu.xml',
    ],
    'installable': True,
    'application': False,
    'auto_install': False,
}
