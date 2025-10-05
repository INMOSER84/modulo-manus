# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, UserError
import qrcode
import io
import base64
from PIL import Image


class ServiceEquipment(models.Model):
    _name = 'inmoser.service.equipment'
    _description = 'Service Equipment'
    _order = 'name desc'
    _rec_name = 'name'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    # Campos básicos
    name = fields.Char(
        string='Equipment Code',
        help='Código único del equipo (E00001)',
        required=True,
        readonly=True,
        copy=False,
        default=lambda self: _('New'),
        tracking=True
    )
    
    equipment_type = fields.Char(
        string='Equipment Type',
        help='Tipo de equipo (Laptop, Impresora, etc.)',
        required=True,
        tracking=True
    )
    
    brand = fields.Char(
        string='Brand',
        help='Marca del equipo',
        required=True,
        tracking=True
    )
    
    model = fields.Char(
        string='Model',
        help='Modelo del equipo (se llena en sitio)',
        tracking=True
    )
    
    serial_number = fields.Char(
        string='Serial Number',
        help='Número de serie del equipo (técnico)',
        tracking=True
    )
    
    location = fields.Char(
        string='Location',
        help='Ubicación del equipo (técnico)',
        tracking=True
    )
    
    # Relaciones
    partner_id = fields.Many2one(
        'res.partner',
        string='Customer',
        help='Cliente propietario del equipo',
        required=True,
        ondelete='cascade',
        tracking=True
    )
    
    # Campos QR
    qr_code = fields.Binary(
        string='QR Code',
        help='Código QR del equipo',
        readonly=True
    )
    
    qr_code_text = fields.Char(
        string='QR Code Text',
        help='Texto codificado en el QR',
        readonly=True,
        compute='_compute_qr_code_text',
        store=True
    )
    
    # Estado y control
    active = fields.Boolean(
        string='Active',
        default=True,
        help='Si está desmarcado, el equipo no aparecerá en las búsquedas'
    )
    
    state = fields.Selection([
        ('draft', 'Draft'),
        ('active', 'Active'),
        ('maintenance', 'In Maintenance'),
        ('retired', 'Retired')
    ], string='State', default='draft', tracking=True)
    
    # Información adicional
    purchase_date = fields.Date(
        string='Purchase Date',
        help='Fecha de compra del equipo'
    )
    
    warranty_expiry = fields.Date(
        string='Warranty Expiry',
        help='Fecha de vencimiento de la garantía'
    )
    
    notes = fields.Text(
        string='Notes',
        help='Notas adicionales sobre el equipo'
    )
    
    # Relaciones con órdenes de servicio
    service_order_ids = fields.One2many(
        'inmoser.service.order',
        'equipment_id',
        string='Service Orders',
        help='Órdenes de servicio asociadas a este equipo'
    )
    
    # Campos computados
    service_order_count = fields.Integer(
        string='Service Orders Count',
        compute='_compute_service_order_count',
        help='Número total de órdenes de servicio'
    )
    
    last_service_date = fields.Datetime(
        string='Last Service Date',
        compute='_compute_last_service_date',
        help='Fecha del último servicio realizado'
    )
    
    warranty_status = fields.Selection([
        ('valid', 'Under Warranty'),
        ('expired', 'Warranty Expired'),
        ('unknown', 'Unknown')
    ], string='Warranty Status', compute='_compute_warranty_status')

    @api.depends('partner_id.x_inmoser_client_sequence', 'name')
    def _compute_qr_code_text(self):
        """Calcula el texto del código QR combinando secuencias"""
        for equipment in self:
            if equipment.partner_id and equipment.partner_id.x_inmoser_client_sequence and equipment.name != _('New'):
                equipment.qr_code_text = f"{equipment.partner_id.x_inmoser_client_sequence}-{equipment.name}"
            else:
                equipment.qr_code_text = False

    @api.depends('service_order_ids')
    def _compute_service_order_count(self):
        """Calcula el número de órdenes de servicio"""
        for equipment in self:
            equipment.service_order_count = len(equipment.service_order_ids)

    @api.depends('service_order_ids.scheduled_date', 'service_order_ids.state')
    def _compute_last_service_date(self):
        """Calcula la fecha del último servicio"""
        for equipment in self:
            completed_orders = equipment.service_order_ids.filtered(
                lambda o: o.state == 'done' and o.scheduled_date
            )
            if completed_orders:
                equipment.last_service_date = max(completed_orders.mapped('scheduled_date'))
            else:
                equipment.last_service_date = False

    @api.depends('warranty_expiry')
    def _compute_warranty_status(self):
        """Calcula el estado de la garantía"""
        today = fields.Date.today()
        for equipment in self:
            if not equipment.warranty_expiry:
                equipment.warranty_status = 'unknown'
            elif equipment.warranty_expiry >= today:
                equipment.warranty_status = 'valid'
            else:
                equipment.warranty_status = 'expired'

    @api.model
    def create(self, vals):
        """Override create para generar secuencia y QR automáticamente"""
        if vals.get('name', _('New')) == _('New'):
            vals['name'] = self.env['ir.sequence'].next_by_code('inmoser.equipment.sequence') or _('New')
        
        equipment = super(ServiceEquipment, self).create(vals)
        equipment._generate_qr_code()
        return equipment

    def write(self, vals):
        """Override write para regenerar QR si cambian datos relevantes"""
        result = super(ServiceEquipment, self).write(vals)
        
        # Regenerar QR si cambian datos que afectan el código
        qr_fields = ['partner_id', 'name']
        if any(field in vals for field in qr_fields):
            for equipment in self:
                equipment._generate_qr_code()
        
        return result

    def _generate_qr_code(self):
        """Genera el código QR para el equipo"""
        for equipment in self:
            if equipment.qr_code_text:
                try:
                    # Crear código QR
                    qr = qrcode.QRCode(
                        version=1,
                        error_correction=qrcode.constants.ERROR_CORRECT_L,
                        box_size=10,
                        border=4,
                    )
                    
                    # URL del portal del cliente para este equipo
                    base_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url')
                    qr_url = f"{base_url}/equipment/{equipment.qr_code_text}"
                    
                    qr.add_data(qr_url)
                    qr.make(fit=True)
                    
                    # Crear imagen
                    img = qr.make_image(fill_color="black", back_color="white")
                    
                    # Convertir a base64
                    buffer = io.BytesIO()
                    img.save(buffer, format='PNG')
                    qr_image = base64.b64encode(buffer.getvalue())
                    
                    equipment.qr_code = qr_image
                    
                except Exception as e:
                    raise UserError(_('Error generating QR code: %s') % str(e))

    def action_generate_qr_code(self):
        """Acción manual para regenerar el código QR"""
        self._generate_qr_code()
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('QR Code Generated'),
                'message': _('QR code has been generated successfully.'),
                'type': 'success',
            }
        }

    def action_view_service_orders(self):
        """Acción para ver las órdenes de servicio del equipo"""
        self.ensure_one()
        action = self.env.ref('inmoser_service_order.action_service_order').read()[0]
        action['domain'] = [('equipment_id', '=', self.id)]
        action['context'] = {
            'default_equipment_id': self.id,
            'default_partner_id': self.partner_id.id,
            'search_default_equipment_id': self.id,
        }
        return action

    def action_create_service_order(self):
        """Acción para crear una nueva orden de servicio para este equipo"""
        self.ensure_one()
        action = self.env.ref('inmoser_service_order.action_service_order').read()[0]
        action['views'] = [(self.env.ref('inmoser_service_order.view_service_order_form').id, 'form')]
        action['context'] = {
            'default_equipment_id': self.id,
            'default_partner_id': self.partner_id.id,
        }
        return action

    def action_set_active(self):
        """Acción para activar el equipo"""
        self.write({'state': 'active'})

    def action_set_maintenance(self):
        """Acción para marcar el equipo en mantenimiento"""
        self.write({'state': 'maintenance'})

    def action_set_retired(self):
        """Acción para retirar el equipo"""
        self.write({'state': 'retired'})

    @api.constrains('serial_number')
    def _check_serial_number_unique(self):
        """Valida que el número de serie sea único por marca y modelo"""
        for equipment in self:
            if equipment.serial_number:
                existing = self.search([
                    ('id', '!=', equipment.id),
                    ('serial_number', '=', equipment.serial_number),
                    ('brand', '=', equipment.brand),
                    ('model', '=', equipment.model)
                ])
                if existing:
                    raise ValidationError(_(
                        'Ya existe un equipo con el mismo número de serie, marca y modelo.'
                    ))

    def name_get(self):
        """Personaliza la visualización del nombre del equipo"""
        result = []
        for equipment in self:
            name = equipment.name or ''
            if equipment.equipment_type and equipment.brand:
                name = f"{name} - {equipment.equipment_type} {equipment.brand}"
                if equipment.model:
                    name += f" {equipment.model}"
            result.append((equipment.id, name))
        return result

    @api.model
    def name_search(self, name='', args=None, operator='ilike', limit=100):
        """Extiende la búsqueda por nombre para incluir marca, modelo y número de serie"""
        args = args or []
        if name:
            # Buscar por código, marca, modelo o número de serie
            equipment_ids = self.search([
                '|', '|', '|',
                ('name', operator, name),
                ('brand', operator, name),
                ('model', operator, name),
                ('serial_number', operator, name)
            ] + args, limit=limit)
            if equipment_ids:
                return equipment_ids.name_get()
        return super(ServiceEquipment, self).name_search(name, args, operator, limit)

