{
    'name': 'Financiero',
    'version': '18.0.1.0.0',
    'category': 'Finance',
    'author': 'Desarrollo',
    'depends': ['base', 'account'],
    'data': [
        'security/ir.model.access.csv',
        'views/medio_magnetico_views.xml',
    ],
    'installable': True,
    'application': True,
}