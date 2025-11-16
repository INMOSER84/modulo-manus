#!/bin/bash
# Script de Corrección y Optimización para el Módulo Odoo: inmoser_service_order
# Creado por Manus - 2025-11-15
# Este script crea o sobrescribe los archivos corregidos y optimizados.

# Directorio base del módulo (ajustar si es necesario)
MODULE_DIR="/home/ubuntu/custom_addons/inmoser_service_order"

echo "=== Iniciando corrección y optimización del módulo inmoser_service_order ==="
mkdir -p "$MODULE_DIR/models"
mkdir -p "$MODULE_DIR/views"
mkdir -p "$MODULE_DIR/data"
mkdir -p "$MODULE_DIR/security"

# ---------------------------------------------------------------------
# 1. __manifest__.py (Corregido: 'license' a LGPL-3, añadido 'web_studio')
# ---------------------------------------------------------------------
echo "-> Creando $MODULE_DIR/__manifest__.py"
sudo tee "$MODULE_DIR/__manifest__.py" > /dev/null << 'EOF'
{
    'name': 'Inmoser Service Order',
    'version': '17.0.1.0.0',
    'summary': 'Service Order Management for Inmoser',
    'description': 'Complete module for managing service orders, equipment, and technicians',
    'category': 'Services',
    'author': 'Inmoser / Manus',
    'website': 'https://www.inmoser.com',
    'license': 'LGPL-3',
    'depends': ['base', 'mail', 'account', 'hr', 'stock', 'web_studio'],
    'external_dependencies': {
        'python': ['qrcode'],
    },
    'data': [
        'security/inmoser_service_order_groups.xml',
        'security/ir.model.access.csv',
        'data/sequences.xml',
        'data/inmoser_service_type_data.xml',
        'data/inmoser_service_order_mail_template.xml',
        'views/res_partner_views.xml',
        'views/hr_employee_views.xml',
        'views/inmoser_service_specialty_views.xml',
        'views/inmoser_service_type_views.xml',
        'views/inmoser_service_equipment_views.xml',
        'views/inmoser_service_order_views.xml',
        'views/menu_views.xml',
    ],
    'installable': True,
    'application': True,
    'auto_install': False,
}
EOF

# ---------------------------------------------------------------------
# 2. models/__init__.py
# ---------------------------------------------------------------------
echo "-> Creando $MODULE_DIR/models/__init__.py"
sudo tee "$MODULE_DIR/models/__init__.py" > /dev/null << 'EOF'
from . import res_partner
from . import hr_employee
from . import inmoser_service_specialty
from . import inmoser_service_type
from . import inmoser_service_equipment
from . import inmoser_service_order
from . import inmoser_service_order_refaction_line
from . import account_move
EOF

# ---------------------------------------------------------------------
# 3. models/res_partner.py (Corregido: Descomentados y optimizados los campos)
# ---------------------------------------------------------------------
echo "-> Creando $MODULE_DIR/models/res_partner.py"
sudo tee "$MODULE_DIR/models/res_partner.py" > /dev/null << 'EOF'
# -*- coding: utf-8 -*-
from odoo import fields, models, api, _

class ResPartner(models.Model):
    _inherit = 'res.partner'

    x_inmoser_client_sequence = fields.Char(
        string='Secuencia de Cliente', 
        copy=False, 
        readonly=True, 
        index=True, 
        default=lambda self: _('New'),
        help='Secuencia automática única para identificar clientes de servicio.'
    )
    x_inmoser_phone_mobile_2 = fields.Char(
        string='Teléfono Celular Adicional',
        help='Teléfono celular adicional del cliente.'
    )
    x_inmoser_is_service_client = fields.Boolean(
        string='Es Cliente de Servicios', 
        default=False, 
        help='Marca si el contacto es un cliente activo para órdenes de servicio.'
    )
    x_inmoser_client_notes = fields.Text(
        string='Notas del Cliente'
    )
    inmoser_equipment_ids = fields.One2many(
        'inmoser.service.equipment', 
        'partner_id', 
        string='Equipos de Servicio'
    )

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('x_inmoser_client_sequence', _('New')) == _('New'):
                vals['x_inmoser_client_sequence'] = self.env['ir.sequence'].next_by_code('res.partner.client.sequence') or _('New')
        return super().create(vals_list)
EOF

# ---------------------------------------------------------------------
# 4. models/hr_employee.py (Corregido: Añadido campo specialties_ids)
# ---------------------------------------------------------------------
echo "-> Creando $MODULE_DIR/models/hr_employee.py"
sudo tee "$MODULE_DIR/models/hr_employee.py" > /dev/null << 'EOF'
# -*- coding: utf-8 -*-
from odoo import fields, models

class HrEmployee(models.Model):
    _inherit = 'hr.employee'

    x_inmoser_is_technician = fields.Boolean(
        string='Es Técnico de Servicio',
        default=False,
        help='Marca si el empleado puede ser asignado a órdenes de servicio.'
    )
    x_inmoser_virtual_warehouse_id = fields.Many2one(
        'stock.warehouse',
        string='Almacén Virtual de Técnico',
        help='Almacén para gestionar el stock del técnico (ej. refacciones).'
    )
    x_inmoser_available_hours = fields.Char(
        string='Horas Disponibles',
        help='Horario de disponibilidad del técnico.'
    )
    x_inmoser_technician_level = fields.Selection([
        ('junior', 'Junior'),
        ('mid', 'Mid-Level'),
        ('senior', 'Senior'),
    ], string='Nivel de Técnico', default='junior')
    
    specialties_ids = fields.Many2many(
        'inmoser.service.specialty',
        'hr_employee_specialty_rel',
        'employee_id',
        'specialty_id',
        string='Especialidades'
    )
EOF

# ---------------------------------------------------------------------
# 5. models/inmoser_service_specialty.py (Corregido: Modelo simple)
# ---------------------------------------------------------------------
echo "-> Creando $MODULE_DIR/models/inmoser_service_specialty.py"
sudo tee "$MODULE_DIR/models/inmoser_service_specialty.py" > /dev/null << 'EOF'
# -*- coding: utf-8 -*-
from odoo import fields, models

class InmoserServiceSpecialty(models.Model):
    _name = 'inmoser.service.specialty'
    _description = 'Especialidad de Técnico de Servicio'

    name = fields.Char(string='Nombre de la Especialidad', required=True)
    description = fields.Text(string='Descripción')
EOF

# ---------------------------------------------------------------------
# 6. models/inmoser_service_type.py (Corregido: Modelo simple)
# ---------------------------------------------------------------------
echo "-> Creando $MODULE_DIR/models/inmoser_service_type.py"
sudo tee "$MODULE_DIR/models/inmoser_service_type.py" > /dev/null << 'EOF'
# -*- coding: utf-8 -*-
from odoo import models, fields

class InmoserServiceType(models.Model):
    _name = 'inmoser.service.type'
    _description = 'Tipo de Servicio Inmoser'
    _order = 'sequence, name'

    name = fields.Char(
        string='Nombre',
        required=True,
        translate=True
    )
    code = fields.Char(
        string='Código',
        required=True,
        help='Código único para el tipo de servicio'
    )
    description = fields.Text(
        string='Descripción',
        translate=True
    )
    sequence = fields.Integer(
        string='Secuencia',
        default=10
    )
    active = fields.Boolean(
        string='Activo',
        default=True
    )

    _sql_constraints = [
        ('code_unique', 'UNIQUE(code)', 'El código del tipo de servicio debe ser único!')
    ]
EOF

# ---------------------------------------------------------------------
# 7. models/inmoser_service_equipment.py (Corregido: Uso de Binary para QR, función QR)
# ---------------------------------------------------------------------
echo "-> Creando $MODULE_DIR/models/inmoser_service_equipment.py"
sudo tee "$MODULE_DIR/models/inmoser_service_equipment.py" > /dev/null << 'EOF'
# -*- coding: utf-8 -*-
from odoo import fields, models, api, _
from odoo.exceptions import UserError
import base64
import io

try:
    import qrcode
except ImportError:
    qrcode = None

class InmoserServiceEquipment(models.Model):
    _name = 'inmoser.service.equipment'
    _description = 'Equipo de Cliente para Servicio'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'name'

    name = fields.Char(
        string='Identificador', 
        required=True, 
        copy=False, 
        readonly=True, 
        index=True, 
        default=lambda self: _('New')
    )
    equipment_type = fields.Char(string='Tipo de Equipo', required=True)
    brand = fields.Char(string='Marca', required=True)
    model = fields.Char(string='Modelo')
    serial_number = fields.Char(string='Número de Serie')
    location = fields.Char(string='Ubicación')
    partner_id = fields.Many2one(
        'res.partner', 
        string='Cliente Propietario', 
        required=True,
        ondelete='restrict'
    )
    purchase_date = fields.Date(string='Fecha de Compra')
    warranty_end_date = fields.Date(string='Fin de Garantía')
    
    # Campos para QR
    qr_code_text = fields.Char(
        string='Texto para QR',
        compute='_compute_qr_code_text',
        store=True,
        readonly=False,
        help='El texto que se codificará en el código QR. Por defecto es el identificador del equipo.'
    )
    qr_code = fields.Binary(
        string='Código QR',
        readonly=True,
        help='Imagen del código QR generado.'
    )

    @api.depends('name', 'serial_number')
    def _compute_qr_code_text(self):
        for record in self:
            if not record.qr_code_text:
                record.qr_code_text = record.name or ''

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name', _('New')) == _('New'):
                vals['name'] = self.env['ir.sequence'].next_by_code('inmoser.service.equipment') or _('New')
        return super().create(vals_list)

    def action_generate_qr(self):
        """Genera el código QR basado en el campo qr_code_text."""
        if not qrcode:
            raise UserError(_("La librería 'qrcode' no está instalada. Por favor, instálela."))
        
        for record in self:
            if not record.qr_code_text:
                raise UserError(_("El campo 'Texto para QR' no puede estar vacío."))
            
            qr = qrcode.QRCode(
                version=1,
                error_correction=qrcode.constants.ERROR_CORRECT_L,
                box_size=10,
                border=4,
            )
            qr.add_data(record.qr_code_text)
            qr.make(fit=True)

            img = qr.make_image(fill_color="black", back_color="white")
            
            # Guardar la imagen en un buffer de bytes
            buffer = io.BytesIO()
            img.save(buffer, format="PNG")
            
            # Codificar a base64 para el campo Binary de Odoo
            record.qr_code = base64.b64encode(buffer.getvalue())
            
        return True
EOF

# ---------------------------------------------------------------------
# 8. models/inmoser_service_order_refaction_line.py (Corregido: Uso de One2many, campo name, compute)
# ---------------------------------------------------------------------
echo "-> Creando $MODULE_DIR/models/inmoser_service_order_refaction_line.py"
sudo tee "$MODULE_DIR/models/inmoser_service_order_refaction_line.py" > /dev/null << 'EOF'
# -*- coding: utf-8 -*-
from odoo import models, fields, api

class InmoserServiceOrderRefactionLine(models.Model):
    _name = 'inmoser.service.order.refaction.line'
    _description = 'Línea de Refacción de Orden de Servicio'

    order_id = fields.Many2one(
        'inmoser.service.order',
        string='Orden de Servicio',
        required=True,
        ondelete='cascade'
    )
    product_id = fields.Many2one(
        'product.product',
        string='Producto/Refacción',
        required=True
    )
    name = fields.Char(
        string='Descripción',
        compute='_compute_name',
        store=True,
        readonly=False,
        help='Descripción de la refacción o servicio.'
    )
    quantity = fields.Float(
        string='Cantidad',
        required=True,
        default=1.0
    )
    price_unit = fields.Float(
        string='Precio Unitario',
        required=True
    )
    price_subtotal = fields.Monetary(
        string='Subtotal',
        compute='_compute_price_subtotal',
        store=True
    )
    currency_id = fields.Many2one(
        related='order_id.currency_id',
        store=True
    )

    @api.depends('product_id')
    def _compute_name(self):
        for line in self:
            if line.product_id and not line.name:
                line.name = line.product_id.name

    @api.depends('quantity', 'price_unit')
    def _compute_price_subtotal(self):
        for line in self:
            line.price_subtotal = line.quantity * line.price_unit
EOF

# ---------------------------------------------------------------------
# 9. models/inmoser_service_order.py (Corregido: Campos, compute, lógica de estados, facturación)
# ---------------------------------------------------------------------
echo "-> Creando $MODULE_DIR/models/inmoser_service_order.py"
sudo tee "$MODULE_DIR/models/inmoser_service_order.py" > /dev/null << 'EOF'
# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
from odoo.tools import float_compare

class InmoserServiceOrder(models.Model):
    _name = 'inmoser.service.order'
    _description = 'Orden de Servicio Inmoser'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'create_date desc'

    # Campos principales
    name = fields.Char(
        string='Número OS', required=True, copy=False,
        readonly=True, index=True, default=lambda self: _('New')
    )
    partner_id = fields.Many2one(
        'res.partner', string='Cliente', required=True,
        tracking=True, domain="[('customer_rank', '>', 0)]"
    )
    equipment_id = fields.Many2one(
        'inmoser.service.equipment', string='Equipo',
        domain="[('partner_id', '=', partner_id)]"
    )
    service_type_id = fields.Many2one(
        'inmoser.service.type', string='Tipo de Servicio', required=True
    )
    assigned_technician_id = fields.Many2one(
        'hr.employee', string='Técnico Asignado',
        domain="[('x_inmoser_is_technician', '=', True)]",
        tracking=True
    )
    
    # Fechas
    date_scheduled = fields.Datetime(string='Fecha Programada')
    date_start = fields.Datetime(string='Fecha Inicio Real', readonly=True)
    date_end = fields.Datetime(string='Fecha Fin Real', readonly=True)

    # Estados
    state = fields.Selection([
        ('draft', 'Borrador'),
        ('confirmed', 'Confirmado'),
        ('assigned', 'Asignado'),
        ('in_progress', 'En Progreso'),
        ('waiting_approval', 'Esperando Aprobación'),
        ('approved', 'Aprobado'),
        ('completed', 'Completado'),
        ('cancelled', 'Cancelado'),
    ], string='Estado', default='draft', tracking=True)

    # Totales
    refaction_total = fields.Monetary(
        string='Total Refacciones',
        compute='_compute_totals',
        store=True
    )
    labor_hours = fields.Float(string='Horas de Mano de Obra')
    labor_price = fields.Monetary(string='Precio por Hora')
    labor_total = fields.Monetary(
        string='Total Mano de Obra', 
        compute='_compute_totals', 
        store=True
    )
    total_amount = fields.Monetary(
        string='Total General', 
        compute='_compute_totals', 
        store=True
    )
    currency_id = fields.Many2one(
        'res.currency', 
        string='Moneda', 
        default=lambda self: self.env.company.currency_id
    )

    # Líneas de refacción (Corregido el nombre del campo)
    service_order_line_ids = fields.One2many(
        'inmoser.service.order.refaction.line', 'order_id',
        string='Líneas de Refacción'
    )

    # Descripción y Resultados
    reported_fault = fields.Text(string='Falla Reportada', required=True)
    diagnosis = fields.Text(string='Diagnóstico del Técnico')
    work_performed = fields.Text(string='Trabajo Realizado')
    
    # Facturación
    invoice_id = fields.Many2one(
        'account.move', 
        string='Factura Creada', 
        readonly=True,
        copy=False
    )
    invoice_count = fields.Integer(
        string='Conteo de Facturas', 
        compute='_compute_invoice_count'
    )

    # Secuencia
    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name', _('New')) == _('New'):
                vals['name'] = self.env['ir.sequence'].next_by_code('inmoser.service.order') or _('New')
        return super().create(vals_list)

    # Computación de Totales
    @api.depends('service_order_line_ids.price_subtotal', 'labor_hours', 'labor_price')
    def _compute_totals(self):
        for order in self:
            refaction_total = sum(order.service_order_line_ids.mapped('price_subtotal'))
            labor_total = order.labor_hours * order.labor_price
            order.refaction_total = refaction_total
            order.labor_total = labor_total
            order.total_amount = refaction_total + labor_total

    # Acciones de estado
    def action_confirm(self):
        self.ensure_one()
        if self.state != 'draft':
            raise UserError(_('Solo se pueden confirmar órdenes en borrador.'))
        self.state = 'confirmed'

    def action_assign(self):
        self.ensure_one()
        if self.state not in ('confirmed', 'assigned'):
            raise UserError(_('Solo se pueden asignar órdenes confirmadas.'))
        if not self.assigned_technician_id:
            raise UserError(_('Debe asignar un técnico antes de cambiar el estado a Asignado.'))
        self.state = 'assigned'

    def action_start(self):
        self.ensure_one()
        if self.state not in ('assigned', 'in_progress'):
            raise UserError(_('Solo se pueden iniciar órdenes asignadas.'))
        if not self.date_start:
            self.date_start = fields.Datetime.now()
        self.state = 'in_progress'

    def action_request_approval(self):
        self.ensure_one()
        if self.state != 'in_progress':
            raise UserError(_('Solo se puede solicitar aprobación para órdenes en progreso.'))
        # Lógica para enviar correo de aprobación (usando la plantilla)
        template = self.env.ref('inmoser_service_order.email_template_customer_approval', raise_if_not_found=False)
        if template:
            template.send_mail(self.id, force_send=True)
        self.state = 'waiting_approval'

    def action_approve(self):
        self.ensure_one()
        if self.state != 'waiting_approval':
            raise UserError(_('Solo se pueden aprobar órdenes en estado de Esperando Aprobación.'))
        self.state = 'approved'

    def action_complete(self):
        self.ensure_one()
        if self.state not in ('in_progress', 'approved'):
            raise UserError(_('Solo se pueden completar órdenes en progreso o aprobadas.'))
        if not self.work_performed:
            raise UserError(_('Debe describir el trabajo realizado antes de completar la orden.'))
        if not self.date_end:
            self.date_end = fields.Datetime.now()
        self.state = 'completed'
        
        # Lógica de facturación automática si aplica
        if float_compare(self.total_amount, 0.0, precision_digits=2) > 0 and not self.invoice_id:
            self._create_invoice()

    def action_cancel(self):
        self.ensure_one()
        if self.state == 'completed':
            raise UserError(_('No se puede cancelar una orden ya completada.'))
        self.state = 'cancelled'

    # Lógica de Facturación
    def _create_invoice(self):
        self.ensure_one()
        if not self.partner_id.property_product_pricelist:
            raise UserError(_('El cliente no tiene una lista de precios definida.'))

        invoice_lines = []
        
        # Líneas de refacciones
        for line in self.service_order_line_ids:
            invoice_lines.append((0, 0, {
                'product_id': line.product_id.id,
                'name': line.name,
                'quantity': line.quantity,
                'price_unit': line.price_unit,
            }))

        # Línea de mano de obra
        if float_compare(self.labor_hours, 0.0, precision_digits=2) > 0:
            labor_product = self.env.ref('inmoser_service_order.product_labor_service', raise_if_not_found=False)
            if not labor_product:
                raise UserError(_("No se encontró el producto de servicio 'Mano de Obra'. Asegúrese de que el registro externo 'product_labor_service' esté creado."))
            
            invoice_lines.append((0, 0, {
                'product_id': labor_product.id,
                'name': _('Mano de Obra: %s horas') % self.labor_hours,
                'quantity': self.labor_hours,
                'price_unit': self.labor_price,
            }))

        if not invoice_lines:
            raise UserError(_('No hay líneas de refacción o mano de obra para facturar.'))

        # Crear factura
        invoice_vals = {
            'partner_id': self.partner_id.id,
            'move_type': 'out_invoice',
            'invoice_line_ids': invoice_lines,
            'service_order_id': self.id, # Campo añadido en account_move.py
        }

        invoice = self.env['account.move'].create(invoice_vals)
        self.invoice_id = invoice.id
        return invoice

    def action_view_invoice(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'account.move',
            'res_id': self.invoice_id.id,
            'view_mode': 'form',
            'target': 'current',
        }

    def _compute_invoice_count(self):
        for order in self:
            order.invoice_count = self.env['account.move'].search_count([('service_order_id', '=', order.id)])

    @api.constrains('date_start', 'date_end')
    def _check_dates(self):
        for order in self:
            if order.date_start and order.date_end:
                if order.date_end < order.date_start:
                    raise ValidationError(_('La fecha de fin debe ser posterior a la fecha de inicio.'))
EOF

# ---------------------------------------------------------------------
# 10. models/account_move.py (Corregido: Extensión de account.move)
# ---------------------------------------------------------------------
echo "-> Creando $MODULE_DIR/models/account_move.py"
sudo tee "$MODULE_DIR/models/account_move.py" > /dev/null << 'EOF'
# -*- coding: utf-8 -*-
from odoo import fields, models

class AccountMove(models.Model):
    _inherit = 'account.move'

    service_order_id = fields.Many2one(
        'inmoser.service.order',
        string='Orden de Servicio',
        readonly=True,
        copy=False,
        help='Orden de Servicio de Inmoser relacionada con esta factura.'
    )
EOF

# ---------------------------------------------------------------------
# 11. data/sequences.xml (Corregido: Añadida secuencia para equipos y clientes)
# ---------------------------------------------------------------------
echo "-> Creando $MODULE_DIR/data/sequences.xml"
sudo tee "$MODULE_DIR/data/sequences.xml" > /dev/null << 'EOF'
<?xml version="1.0" encoding="utf-8"?>
<odoo noupdate="1">
    <!-- Secuencia para Órdenes de Servicio (inmoser.service.order) -->
    <record id="sequence_service_order" model="ir.sequence">
        <field name="name">Orden de Servicio Inmoser</field>
        <field name="code">inmoser.service.order</field>
        <field name="prefix">OS%(year)s</field>
        <field name="padding">5</field>
        <field name="company_id" eval="False"/>
    </record>

    <!-- Secuencia para Equipos (inmoser.service.equipment) -->
    <record id="sequence_service_equipment" model="ir.sequence">
        <field name="name">Equipo de Servicio Inmoser</field>
        <field name="code">inmoser.service.equipment</field>
        <field name="prefix">EQ</field>
        <field name="padding">5</field>
        <field name="company_id" eval="False"/>
    </record>

    <!-- Secuencia para Clientes (res.partner) -->
    <record id="sequence_res_partner_client" model="ir.sequence">
        <field name="name">Secuencia de Cliente Inmoser</field>
        <field name="code">res.partner.client.sequence</field>
        <field name="prefix">CLI</field>
        <field name="padding">5</field>
        <field name="company_id" eval="False"/>
    </record>
</odoo>
EOF

# ---------------------------------------------------------------------
# 12. data/inmoser_service_type_data.xml (Corregido: Modelo simple)
# ---------------------------------------------------------------------
echo "-> Creando $MODULE_DIR/data/inmoser_service_type_data.xml"
sudo tee "$MODULE_DIR/data/inmoser_service_type_data.xml" > /dev/null << 'EOF'
<?xml version="1.0" encoding="utf-8"?>
<odoo noupdate="1">
    <record id="service_type_preventive" model="inmoser.service.type">
        <field name="name">Mantenimiento Preventivo</field>
        <field name="code">PREVENTIVE</field>
        <field name="description">Mantenimiento preventivo regular de equipos</field>
        <field name="sequence">10</field>
    </record>

    <record id="service_type_corrective" model="inmoser.service.type">
        <field name="name">Mantenimiento Correctivo</field>
        <field name="code">CORRECTIVE</field>
        <field name="description">Reparación de equipos con fallo</field>
        <field name="sequence">20</field>
    </record>

    <record id="service_type_emergency" model="inmoser.service.type">
        <field name="name">Servicio de Emergencia</field>
        <field name="code">EMERGENCY</field>
        <field name="description">Servicio de reparación urgente</field>
        <field name="sequence">30</field>
    </record>
    
    <!-- Producto de servicio para Mano de Obra -->
    <record id="product_labor_service" model="product.product">
        <field name="name">Mano de Obra de Servicio</field>
        <field name="type">service</field>
        <field name="default_code">LABOR</field>
        <field name="list_price">0.0</field>
        <field name="invoice_policy">delivery</field>
        <field name="uom_id" ref="uom.product_uom_hour"/>
        <field name="uom_po_id" ref="uom.product_uom_hour"/>
    </record>
</odoo>
EOF

# ---------------------------------------------------------------------
# 13. data/inmoser_service_order_mail_template.xml (Corregido: Uso de campos correctos)
# ---------------------------------------------------------------------
echo "-> Creando $MODULE_DIR/data/inmoser_service_order_mail_template.xml"
sudo tee "$MODULE_DIR/data/inmoser_service_order_mail_template.xml" > /dev/null << 'EOF'
<?xml version="1.0" encoding="utf-8"?>
<odoo>
    <record id="email_template_customer_approval" model="mail.template">
        <field name="name">Inmoser: Solicitud de Aprobación de Servicio</field>
        <field name="model_id" ref="model_inmoser_service_order"/>
        <field name="email_from">${object.company_id.email_formatted or user.email_formatted}</field>
        <field name="email_to">${object.partner_id.email_formatted}</field>
        <field name="subject">Solicitud de Aprobación - Orden de Servicio ${object.name}</field>
        <field name="body_html" type="html">
<div style="margin: 0px; padding: 0px; font-size: 13px;">
    <p>Estimado/a ${object.partner_id.name},</p>
    <p>Le informamos que se ha realizado el diagnóstico de su equipo <strong>${object.equipment_id.name}</strong> (Serial: ${object.equipment_id.serial_number or 'N/A'}).</p>
    
    <p><strong>Orden de Servicio:</strong> ${object.name}</p>
    <p><strong>Falla Reportada:</strong> ${object.reported_fault or 'N/A'}</p>
    <p><strong>Diagnóstico del Técnico:</strong> ${object.diagnosis or 'N/A'}</p>
    
    <p><strong>Monto Estimado Total:</strong> ${object.total_amount} ${object.currency_id.symbol}</p>
    
    <p>Por favor, acceda al portal para revisar los detalles y aprobar o rechazar el servicio. Si no tiene acceso al portal, por favor contacte a nuestro equipo.</p>
    
    <p>Gracias por su confianza.</p>
</div>
        </field>
    </record>
</odoo>
EOF

# ---------------------------------------------------------------------
# 14. views/res_partner_views.xml (Corregido: Añadida vista para campos de res.partner)
# ---------------------------------------------------------------------
echo "-> Creando $MODULE_DIR/views/res_partner_views.xml"
sudo tee "$MODULE_DIR/views/res_partner_views.xml" > /dev/null << 'EOF'
<?xml version="1.0" encoding="utf-8"?>
<odoo>
    <record id="view_partner_form_inmoser_extension" model="ir.ui.view">
        <field name="name">res.partner.form.inmoser.extension</field>
        <field name="model">res.partner</field>
        <field name="inherit_id" ref="base.view_partner_form"/>
        <field name="arch" type="xml">
            <xpath expr="//field[@name='category_id']" position="after">
                <field name="x_inmoser_is_service_client"/>
            </xpath>
            <xpath expr="//page[@name='sales_purchases']" position="after">
                <page string="Servicio Inmoser" name="inmoser_service" attrs="{'invisible': [('x_inmoser_is_service_client', '=', False)]}">
                    <group>
                        <group>
                            <field name="x_inmoser_client_sequence"/>
                            <field name="x_inmoser_phone_mobile_2"/>
                        </group>
                        <group>
                            <field name="x_inmoser_client_notes"/>
                        </group>
                    </group>
                    <separator string="Equipos de Servicio"/>
                    <field name="inmoser_equipment_ids" context="{'default_partner_id': active_id}">
                        <tree editable="bottom">
                            <field name="name"/>
                            <field name="equipment_type"/>
                            <field name="brand"/>
                            <field name="model"/>
                            <field name="serial_number"/>
                        </tree>
                    </field>
                </page>
            </xpath>
        </field>
    </record>
</odoo>
EOF

# ---------------------------------------------------------------------
# 15. views/hr_employee_views.xml (Corregido: Añadida vista para campos de hr.employee)
# ---------------------------------------------------------------------
echo "-> Creando $MODULE_DIR/views/hr_employee_views.xml"
sudo tee "$MODULE_DIR/views/hr_employee_views.xml" > /dev/null << 'EOF'
<?xml version="1.0" encoding="utf-8"?>
<odoo>
    <record id="view_employee_form_inmoser_extension" model="ir.ui.view">
        <field name="name">hr.employee.form.inmoser.extension</field>
        <field name="model">hr.employee</field>
        <field name="inherit_id" ref="hr.view_employee_form"/>
        <field name="arch" type="xml">
            <xpath expr="//page[@name='personal_information']" position="after">
                <page string="Técnico de Servicio" name="inmoser_technician">
                    <group>
                        <group>
                            <field name="x_inmoser_is_technician"/>
                            <field name="x_inmoser_technician_level" attrs="{'invisible': [('x_inmoser_is_technician', '=', False)]}"/>
                            <field name="x_inmoser_available_hours" attrs="{'invisible': [('x_inmoser_is_technician', '=', False)]}"/>
                        </group>
                        <group>
                            <field name="x_inmoser_virtual_warehouse_id" attrs="{'invisible': [('x_inmoser_is_technician', '=', False)]}"/>
                        </group>
                    </group>
                    <separator string="Especialidades" attrs="{'invisible': [('x_inmoser_is_technician', '=', False)]}"/>
                    <field name="specialties_ids" widget="many2many_tags" attrs="{'invisible': [('x_inmoser_is_technician', '=', False)]}"/>
                </page>
            </xpath>
        </field>
    </record>
</odoo>
EOF

# ---------------------------------------------------------------------
# 16. views/inmoser_service_specialty_views.xml (Corregido: Vista simple)
# ---------------------------------------------------------------------
echo "-> Creando $MODULE_DIR/views/inmoser_service_specialty_views.xml"
sudo tee "$MODULE_DIR/views/inmoser_service_specialty_views.xml" > /dev/null << 'EOF'
<?xml version="1.0" encoding="utf-8"?>
<odoo>
    <record id="view_inmoser_service_specialty_tree" model="ir.ui.view">
        <field name="name">inmoser.service.specialty.tree</field>
        <field name="model">inmoser.service.specialty</field>
        <field name="arch" type="xml">
            <tree string="Especialidades de Servicio">
                <field name="name"/>
                <field name="description"/>
            </tree>
        </field>
    </record>

    <record id="view_inmoser_service_specialty_form" model="ir.ui.view">
        <field name="name">inmoser.service.specialty.form</field>
        <field name="model">inmoser.service.specialty</field>
        <field name="arch" type="xml">
            <form string="Especialidad de Servicio">
                <sheet>
                    <group>
                        <field name="name"/>
                        <field name="description"/>
                    </group>
                </sheet>
            </form>
        </field>
    </record>

    <record id="action_inmoser_specialty" model="ir.actions.act_window">
        <field name="name">Especialidades de Servicio</field>
        <field name="res_model">inmoser.service.specialty</field>
        <field name="view_mode">tree,form</field>
    </record>
</odoo>
EOF

# ---------------------------------------------------------------------
# 17. views/inmoser_service_type_views.xml (Corregido: Vista simple)
# ---------------------------------------------------------------------
echo "-> Creando $MODULE_DIR/views/inmoser_service_type_views.xml"
sudo tee "$MODULE_DIR/views/inmoser_service_type_views.xml" > /dev/null << 'EOF'
<?xml version="1.0" encoding="utf-8"?>
<odoo>
    <record id="view_inmoser_service_type_tree" model="ir.ui.view">
        <field name="name">inmoser.service.type.tree</field>
        <field name="model">inmoser.service.type</field>
        <field name="arch" type="xml">
            <tree string="Tipos de Servicio">
                <field name="sequence" widget="handle"/>
                <field name="name"/>
                <field name="code"/>
                <field name="active" widget="boolean_toggle"/>
            </tree>
        </field>
    </record>

    <record id="view_inmoser_service_type_form" model="ir.ui.view">
        <field name="name">inmoser.service.type.form</field>
        <field name="model">inmoser.service.type</field>
        <field name="arch" type="xml">
            <form string="Tipo de Servicio">
                <sheet>
                    <group>
                        <group>
                            <field name="name"/>
                            <field name="code"/>
                            <field name="sequence"/>
                        </group>
                        <group>
                            <field name="active"/>
                        </group>
                    </group>
                    <field name="description"/>
                </sheet>
            </form>
        </field>
    </record>

    <record id="action_inmoser_service_type" model="ir.actions.act_window">
        <field name="name">Tipos de Servicio</field>
        <field name="res_model">inmoser.service.type</field>
        <field name="view_mode">tree,form</field>
    </record>
</odoo>
EOF

# ---------------------------------------------------------------------
# 18. views/inmoser_service_equipment_views.xml (Corregido: Botón QR, campo qr_code_text)
# ---------------------------------------------------------------------
echo "-> Creando $MODULE_DIR/views/inmoser_service_equipment_views.xml"
sudo tee "$MODULE_DIR/views/inmoser_service_equipment_views.xml" > /dev/null << 'EOF'
<?xml version="1.0" encoding="utf-8"?>
<odoo>
    <record id="view_inmoser_service_equipment_tree" model="ir.ui.view">
        <field name="name">inmoser.service.equipment.tree</field>
        <field name="model">inmoser.service.equipment</field>
        <field name="arch" type="xml">
            <tree string="Equipos de Servicio">
                <field name="name"/>
                <field name="equipment_type"/>
                <field name="brand"/>
                <field name="model"/>
                <field name="serial_number"/>
                <field name="partner_id"/>
            </tree>
        </field>
    </record>

    <record id="view_inmoser_service_equipment_form" model="ir.ui.view">
        <field name="name">inmoser.service.equipment.form</field>
        <field name="model">inmoser.service.equipment</field>
        <field name="arch" type="xml">
            <form string="Equipo de Servicio">
                <sheet>
                    <div class="oe_button_box" name="button_box">
                        <button name="action_generate_qr"
                                type="object"
                                string="Generar QR"
                                icon="fa-qrcode"
                                class="oe_stat_button"
                                help="Generar Código QR para el equipo"/>
                    </div>
                    <div class="oe_title">
                        <h1><field name="name" readonly="1"/></h1>
                    </div>
                    <group>
                        <group>
                            <field name="equipment_type"/>
                            <field name="brand"/>
                            <field name="model"/>
                            <field name="serial_number"/>
                        </group>
                        <group>
                            <field name="partner_id"/>
                            <field name="purchase_date"/>
                            <field name="warranty_end_date"/>
                        </group>
                    </group>
                    <notebook>
                        <page string="QR Code">
                            <group>
                                <group>
                                    <field name="qr_code_text" placeholder="Texto para el QR (ej. URL o ID)"/>
                                </group>
                                <group>
                                    <field name="qr_code" widget="image" class="oe_avatar" nolabel="1"/>
                                </group>
                            </group>
                        </page>
                    </notebook>
                </sheet>
                <div class="oe_chatter">
                    <field name="message_follower_ids" widget="mail_followers"/>
                    <field name="activity_ids" widget="mail_activity"/>
                    <field name="message_ids" widget="mail_thread"/>
                </div>
            </form>
        </field>
    </record>

    <record id="action_inmoser_equipment" model="ir.actions.act_window">
        <field name="name">Equipos</field>
        <field name="res_model">inmoser.service.equipment</field>
        <field name="view_mode">tree,form</field>
    </record>
</odoo>
EOF

# ---------------------------------------------------------------------
# 19. views/inmoser_service_order_views.xml (Corregido: Campos, botones, contadores)
# ---------------------------------------------------------------------
echo "-> Creando $MODULE_DIR/views/inmoser_service_order_views.xml"
sudo tee "$MODULE_DIR/views/inmoser_service_order_views.xml" > /dev/null << 'EOF'
<?xml version="1.0" encoding="utf-8"?>
<odoo>
    <!-- VISTA FORM -->
    <record id="view_inmoser_service_order_form" model="ir.ui.view">
        <field name="name">inmoser.service.order.form</field>
        <field name="model">inmoser.service.order</field>
        <field name="arch" type="xml">
            <form string="Orden de Servicio">
                <header>
                    <button name="action_confirm" type="object" string="Confirmar" class="oe_highlight" states="draft"/>
                    <button name="action_assign" type="object" string="Asignar" class="oe_highlight" states="confirmed" attrs="{'invisible': [('assigned_technician_id', '=', False)]}"/>
                    <button name="action_start" type="object" string="Iniciar Servicio" class="oe_highlight" states="assigned,in_progress"/>
                    <button name="action_request_approval" type="object" string="Solicitar Aprobación" states="in_progress"/>
                    <button name="action_approve" type="object" string="Aprobar" class="oe_highlight" states="waiting_approval"/>
                    <button name="action_complete" type="object" string="Completar" class="oe_highlight" states="in_progress,approved"/>
                    <button name="action_cancel" type="object" string="Cancelar" states="draft,confirmed,assigned,in_progress,waiting_approval"/>
                    <field name="state" widget="statusbar" statusbar_visible="draft,assigned,in_progress,completed"/>
                </header>
                <sheet>
                    <div class="oe_button_box" name="button_box">
                        <button name="action_view_invoice"
                                type="object"
                                class="oe_stat_button"
                                icon="fa-pencil-square-o"
                                attrs="{'invisible': [('invoice_count', '=', 0)]}">
                            <field name="invoice_count" widget="statinfo" string="Facturas"/>
                        </button>
                    </div>
                    <div class="oe_title">
                        <h1>
                            <field name="name" readonly="1" default_focus="1" placeholder="Nueva OS"/>
                        </h1>
                    </div>
                    <group>
                        <group>
                            <field name="partner_id" options='{"no_open": False}'/>
                            <field name="equipment_id" options='{"no_open": False}' domain="[('partner_id', '=', partner_id)]"/>
                            <field name="service_type_id" options='{"no_open": False}'/>
                        </group>
                        <group>
                            <field name="assigned_technician_id" options="{&quot;no_open&quot;: False}" domain="[('x_inmoser_is_technician', '=', True)]"/>
                            <field name="date_scheduled"/>
                            <field name="date_start" readonly="1"/>
                            <field name="date_end" readonly="1"/>
                        </group>
                    </group>
                    <field name="reported_fault" placeholder="Describa la falla reportada por el cliente..." required="1"/>
                    <notebook>
                        <page string="Refacciones y Costos" name="refactions_costs">
                            <field name="service_order_line_ids">
                                <tree editable="bottom">
                                    <field name="product_id" options='{"no_open": False}'/>
                                    <field name="name"/>
                                    <field name="quantity"/>
                                    <field name="price_unit"/>
                                    <field name="price_subtotal" readonly="1" sum="Total"/>
                                </tree>
                            </field>
                            <group class="oe_subtotal_footer oe_right">
                                <field name="refaction_total" widget="monetary" options="{'currency_field': 'currency_id'}"/>
                                <field name="labor_hours" widget="float_time"/>
                                <field name="labor_price" widget="monetary" options="{'currency_field': 'currency_id'}"/>
                                <field name="labor_total" widget="monetary" options="{'currency_field': 'currency_id'}"/>
                                <div class="oe_subtotal_footer_separator oe_inline">
                                    <label for="total_amount"/>
                                    <button name="action_view_invoice" type="object" class="oe_link" string="(Ver Factura)" attrs="{'invisible': [('invoice_id', '=', False)]}"/>
                                </div>
                                <field name="total_amount" nolabel="1" class="oe_subtotal_footer_separator" widget="monetary" options="{'currency_field': 'currency_id'}"/>
                                <field name="currency_id" invisible="1"/>
                            </group>
                        </page>
                        <page string="Diagnóstico y Trabajo" name="diagnosis_work">
                            <group>
                                <field name="diagnosis" placeholder="Describa el diagnóstico del equipo..."/>
                                <field name="work_performed" placeholder="Describa el trabajo realizado..."/>
                            </group>
                        </page>
                        <page string="Facturación" name="invoicing">
                            <group>
                                <field name="invoice_id" readonly="1"/>
                                <button name="action_create_invoice" type="object" string="Crear Factura Manualmente" class="oe_highlight" attrs="{'invisible': ['|', ('state', '!=', 'completed'), ('invoice_id', '!=', False)]}"/>
                            </group>
                        </page>
                    </notebook>
                </sheet>
                <div class="oe_chatter">
                    <field name="message_follower_ids" widget="mail_followers"/>
                    <field name="activity_ids" widget="mail_activity"/>
                    <field name="message_ids" widget="mail_thread"/>
                </div>
            </form>
        </field>
    </record>

    <!-- VISTA TREE -->
    <record id="view_inmoser_service_order_tree" model="ir.ui.view">
        <field name="name">inmoser.service.order.tree</field>
        <field name="model">inmoser.service.order</field>
        <field name="arch" type="xml">
            <tree string="Órdenes de Servicio" decoration-muted="state == 'cancelled'" decoration-success="state == 'completed'">
                <field name="name"/>
                <field name="partner_id"/>
                <field name="equipment_id"/>
                <field name="service_type_id"/>
                <field name="assigned_technician_id"/>
                <field name="date_scheduled"/>
                <field name="state"/>
                <field name="total_amount" sum="Total General"/>
            </tree>
        </field>
    </record>

    <!-- ACTION PRINCIPAL -->
    <record id="action_inmoser_service_order" model="ir.actions.act_window">
        <field name="name">Órdenes de Servicio</field>
        <field name="res_model">inmoser.service.order</field>
        <field name="view_mode">tree,form</field>
        <field name="help" type="html">
            <p class="o_view_nocontent_smiling_face">
                Cree su primera Orden de Servicio
            </p>
        </field>
    </record>
</odoo>
EOF

# ---------------------------------------------------------------------
# 20. views/menu_views.xml (Corregido: Menús)
# ---------------------------------------------------------------------
echo "-> Creando $MODULE_DIR/views/menu_views.xml"
sudo tee "$MODULE_DIR/views/menu_views.xml" > /dev/null << 'EOF'
<?xml version="1.0" encoding="utf-8"?>
<odoo>
    <!-- Menú Raíz -->
    <menuitem id="menu_inmoser_service_root"
              name="Servicio Técnico"
              sequence="10"
              web_icon="fa fa-wrench"/>

    <!-- Submenú Órdenes -->
    <menuitem id="menu_inmoser_service_orders"
              name="Órdenes de Servicio"
              parent="menu_inmoser_service_root"
              sequence="10"/>

    <menuitem id="menu_inmoser_service_order_action"
              name="Órdenes de Servicio"
              parent="menu_inmoser_service_orders"
              action="action_inmoser_service_order"
              sequence="10"/>

    <!-- Submenú Configuración -->
    <menuitem id="menu_inmoser_service_configuration"
              name="Configuración"
              parent="menu_inmoser_service_root"
              sequence="100"
              groups="base.group_system"/>

    <menuitem id="menu_inmoser_service_equipment_action"
              name="Equipos de Cliente"
              parent="menu_inmoser_service_configuration"
              action="action_inmoser_equipment"
              sequence="10"/>

    <menuitem id="menu_inmoser_service_type_action"
              name="Tipos de Servicio"
              parent="menu_inmoser_service_configuration"
              action="action_inmoser_service_type"
              sequence="20"/>

    <menuitem id="menu_inmoser_service_specialty_action"
              name="Especialidades de Técnico"
              parent="menu_inmoser_service_configuration"
              action="action_inmoser_specialty"
              sequence="30"/>
</odoo>
EOF

# ---------------------------------------------------------------------
# 21. security/inmoser_service_order_groups.xml (Corregido: Grupos de seguridad)
# ---------------------------------------------------------------------
echo "-> Creando $MODULE_DIR/security/inmoser_service_order_groups.xml"
sudo tee "$MODULE_DIR/security/inmoser_service_order_groups.xml" > /dev/null << 'EOF'
<?xml version="1.0" encoding="utf-8"?>
<odoo>
    <record id="group_inmoser_user" model="res.groups">
        <field name="name">Usuario de Servicio</field>
        <field name="category_id" ref="base.module_category_services_management"/>
        <field name="implied_ids" eval="[(4, ref('base.group_user'))]"/>
    </record>

    <record id="group_inmoser_technician" model="res.groups">
        <field name="name">Técnico de Servicio</field>
        <field name="category_id" ref="base.module_category_services_management"/>
        <field name="implied_ids" eval="[(4, ref('group_inmoser_user'))]"/>
    </record>

    <record id="group_inmoser_manager" model="res.groups">
        <field name="name">Gerente de Servicio</field>
        <field name="category_id" ref="base.module_category_services_management"/>
        <field name="implied_ids" eval="[(4, ref('group_inmoser_technician'))]"/>
        <field name="users" eval="[(4, ref('base.user_root')), (4, ref('base.user_admin'))]"/>
    </record>
</odoo>
EOF

# ---------------------------------------------------------------------
# 22. security/ir.model.access.csv (Corregido: Reglas de acceso)
# ---------------------------------------------------------------------
echo "-> Creando $MODULE_DIR/security/ir.model.access.csv"
sudo tee "$MODULE_DIR/security/ir.model.access.csv" > /dev/null << 'EOF'
id,name,model_id:id,group_id:id,perm_read,perm_write,perm_create,perm_unlink
access_inmoser_service_order_manager,Orden de Servicio Manager,model_inmoser_service_order,group_inmoser_manager,1,1,1,1
access_inmoser_service_order_technician,Orden de Servicio Technician,model_inmoser_service_order,group_inmoser_technician,1,1,1,0
access_inmoser_service_order_user,Orden de Servicio User,model_inmoser_service_order,group_inmoser_user,1,0,1,0

access_inmoser_service_equipment_manager,Equipo Manager,model_inmoser_service_equipment,group_inmoser_manager,1,1,1,1
access_inmoser_service_equipment_user,Equipo User,model_inmoser_service_equipment,group_inmoser_user,1,1,1,0

access_inmoser_service_type_manager,Tipo de Servicio Manager,model_inmoser_service_type,group_inmoser_manager,1,1,1,1
access_inmoser_service_type_user,Tipo de Servicio User,model_inmoser_service_type,group_inmoser_user,1,0,0,0

access_inmoser_service_specialty_manager,Especialidad Manager,model_inmoser_service_specialty,group_inmoser_manager,1,1,1,1
access_inmoser_service_specialty_user,Especialidad User,model_inmoser_service_specialty,group_inmoser_user,1,0,0,0

access_inmoser_service_order_refaction_line_manager,Línea Refacción Manager,model_inmoser_service_order_refaction_line,group_inmoser_manager,1,1,1,1
access_inmoser_service_order_refaction_line_user,Línea Refacción User,model_inmoser_service_order_refaction_line,group_inmoser_user,1,1,1,0
EOF

echo "=== Corrección y optimización del módulo inmoser_service_order completada. ==="
echo "El script 'fix_inmoser_service_order.sh' ha sido creado en /home/ubuntu/"
echo "Para aplicar los cambios, ejecute: bash /home/ubuntu/fix_inmoser_service_order.sh"
echo "Luego, actualice la lista de módulos y actualice el módulo 'inmoser_service_order' en Odoo."
