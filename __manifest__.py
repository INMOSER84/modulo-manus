{
    'name': 'INMOSER Service Order - Gestión de Servicios, Inventario y Ventas',
    'version': '2.0',
    'summary': 'Sistema completo de gestión de servicios técnicos, inventario y ventas',
    'description': """
Módulo integral para gestión de servicios técnicos, inventario y ventas compatible con Odoo 17 Community Edition
Características principales:
- Gestión de órdenes de servicio técnico
- Control de inventario personalizado
- Validación automática de stock
- Tipos de venta personalizados
- Reportes de ventas y servicios
- Integración con contabilidad
- Portal para clientes
- Generación de códigos QR
    """,
    'author': 'INMOSER84',
    'license': 'LGPL-3',
    'odoo_version': '17.0',
    'depends': ['base', 'product', 'sale', 'account', 'hr', 'stock', 'portal', 'web'],
    'data': [
        'security/inmoser_security.xml',
        'security/ir.model.access.csv',
        'views/menu_items.xml',
        'views/service_order_views.xml',
        'views/service_equipment_views.xml',
        'views/service_type_views.xml',
        'views/hr_employee_views.xml',
        'views/res_partner_views.xml',
        'views/portal_templates.xml',
        'views/service_complete_wizard_views.xml',
        'views/service_reprogram_wizard_views.xml',
        'views/stock_update_wizard_views.xml',
        'reports/service_order_report.xml',
        'reports/service_order_template.xml',
        'reports/equipment_history_template.xml',
        'reports/technician_performance_template.xml',
        'data/service_type_data.xml',
        'data/ir_sequence_data.xml',
        'data/email_templates.xml',
        'data/cron_jobs.xml',
        'static/src/xml/calendar_templates.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'inmoser_manus/static/src/js/calendar_view.js',
            'inmoser_manus/static/src/scss/service_order.scss',
        ],
    },
    'demo': ['demo/demo_data.xml'],
    'installable': True,
    'application': True,
    'auto_install': False,
}
