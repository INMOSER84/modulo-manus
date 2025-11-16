{
    'name': 'Inmoser Field Service',
    'version': '17.0.1.0.0',
    'category': 'Services',
    'summary': 'Field Service Management for Inmoser',
    'description': """
        Extension for Field Service Management linking to OCA industry_fsm
    """,
    'author': 'Your Name / Gemini',
    'website': 'https://www.inmoser.com',
    'license': 'OEEL-1',
    'depends': [
        'inmoser_service_order',
    ],
    'data': [
        'security/ir.model.access.csv',
        'views/fsm_order_views.xml',
    ],
    'installable': True,
    'application': False,
}
