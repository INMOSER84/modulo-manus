{
    'name': 'Gestión de Manuscritos',
    'version': '17.0.1.0.0',
    'category': 'Document Management',
    'summary': 'Gestión integral de manuscritos y documentos antiguos',
    'author': 'INMOSER',
    'website': 'https://github.com/INMOSER84',
    'license': 'LGPL-3',
    'depends': [
        'base',
        'web',
        'mail',
        'hr'
    ],
    'data': [
        'security/manus_security.xml',
        'security/ir.model.access.csv',
        'views/manus_views.xml',
        'data/manus_data.xml'
    ],
    'installable': True,
    'application': True,
    'auto_install': False
}
