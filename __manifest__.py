# -*- coding: utf-8 -*-
{
    'name': 'Inmoser Service Order Management',
    'version': '17.0.1.0.0',
    'category': 'Services/Field Service',
    'summary': 'Gestión integral de órdenes de servicio para Inmoser',
    'description': """
        Módulo completo para la gestión de órdenes de servicio que incluye:
        
        * Gestión de clientes con secuencias automáticas
        * Registro y seguimiento de equipos con códigos QR
        * Flujo completo de órdenes de servicio desde creación hasta facturación
        * Gestión de técnicos con calendarios y almacenes virtuales
        * Portal del cliente para seguimiento y nuevas solicitudes
        * Integración con contabilidad, inventario y recursos humanos
        * Reportes y documentos personalizados
        * Notificaciones automáticas
        
        Desarrollado siguiendo las mejores prácticas de Odoo y estándares Gold Partner.
    """,
    'author': 'Manus AI',
    'website': 'https://www.inmoser.com',
    'license': 'LGPL-3',
    'depends': [
        'base',
        'mail',
        'portal',
        'website',
        'hr',
        'account',
        'stock',
        'sale',
        'purchase',
        'project',
        'crm',
    ],
    'data': [
        # Security
        'security/inmoser_security.xml',
        'security/ir.model.access.csv',
        
        # Data
        'data/ir_sequence_data.xml',
        'data/service_type_data.xml',
        'data/email_templates.xml',
        'data/cron_jobs.xml',
        
        # Views
        'views/res_partner_views.xml',
        'views/hr_employee_views.xml',
        'views/service_equipment_views.xml',
        'views/service_type_views.xml',
        'views/service_order_views.xml',
        'views/service_reprogram_wizard_views.xml',
        'views/service_complete_wizard_views.xml',
        'views/portal_templates.xml',
        'views/menu_items.xml',
        
        # Reports
        'reports/service_order_report.xml',
        'reports/service_order_template.xml',
        'reports/technician_performance_template.xml',
        'reports/equipment_history_template.xml',
    ],
    'demo': [
        'demo/demo_data.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'inmoser_service_order/static/src/scss/service_order.scss',
            'inmoser_service_order/static/src/js/service_order_qr.js',
        ],
        'web.assets_frontend': [
            'inmoser_service_order/static/src/scss/portal.scss',
        ],
    },
    'images': ['static/description/banner.png'],
    'installable': True,
    'application': True,
    'auto_install': False,
    'sequence': 10,
    'external_dependencies': {
        'python': ['qrcode', 'Pillow'],
    },
}

