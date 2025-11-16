#!/bin/bash
set -e  # Detener en cualquier error

# LIMPIAR ARCHIVOS CORRUPTOS
rm -f models/inmoser_*.py

# =====================================================================
# ARCHIVO 1: inmoser_service_order.py (135 líneas)
# =====================================================================
cat > models/inmoser_service_order.py << 'PYFILE001'
# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import UserError

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
    technician_id = fields.Many2one(
        'hr.employee', string='Técnico Asignado',
        domain="[('x_inmoser_is_technician', '=', True)]"
    )

    # Fechas
    date_scheduled = fields.Datetime(string='Fecha Programada')
    date_start = fields.Datetime(string='Fecha Inicio', readonly=True)
    date_end = fields.Datetime(string='Fecha Fin', readonly=True)

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
    total_amount = fields.Monetary(string='Total', currency_field='currency_id', compute='_compute_totals', store=True)
    currency_id = fields.Many2one('res.currency', string='Currency', default=lambda self: self.env.company.currency_id)

    # Líneas de refacción
    refaction_line_ids = fields.One2many(
        'inmoser.service.order.refaction.line', 'order_id',
        string='Líneas de Refacción'
    )
    labor_hours = fields.Float(string='Horas de Mano de Obra')
    labor_price = fields.Monetary(string='Precio por Hora', currency_field='currency_id')
    labor_total = fields.Monetary(string='Total Mano de Obra', currency_field='currency_id', compute='_compute_totals', store=True)

    # Descripción
    diagnosis = fields.Text(string='Diagnóstico')
    work_done = fields.Text(string='Trabajo Realizado')

    # Facturas
    invoice_ids = fields.Many2many(
        'account.move', 'inmoser_service_order_invoice_rel',
        'order_id', 'invoice_id', string='Facturas', readonly=True
    )

    # Secuencia
    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name', _('New')) == _('New'):
                vals['name'] = self.env['ir.sequence'].next_by_code('inmoser.service.order') or _('New')
        return super().create(vals_list)

    # Acciones de estado
    def action_confirm(self):
        for record in self:
            if record.state != 'draft':
                raise UserError(_('Solo se pueden confirmar órdenes en borrador.'))
            record.state = 'confirmed'

    def action_assign(self):
        for record in self:
            if record.state != 'confirmed':
                raise UserError(_('Solo se pueden asignar órdenes confirmadas.'))
            record.state = 'assigned'

    def action_start(self):
        for record in self:
            if record.state != 'assigned':
                raise UserError(_('Solo se pueden iniciar órdenes asignadas.'))
            record.write({
                'state': 'in_progress',
                'date_start': fields.Datetime.now()
            })

    def action_complete(self):
        for record in self:
            if record.state not in ['in_progress', 'waiting_approval']:
                raise UserError(_('Solo se pueden completar órdenes en progreso o aprobadas.'))
            record.write({
                'state': 'completed',
                'date_end': fields.Datetime.now()
            })

    def action_cancel(self):
        for record in self:
            if record.state in ['completed', 'approved']:
                raise UserError(_('No se pueden cancelar órdenes completadas o aprobadas.'))
            record.state = 'cancelled'

    def action_request_approval(self):
        for record in self:
            if record.state != 'in_progress':
                raise UserError(_('Solo se puede solicitar aprobación de órdenes en progreso.'))
            record.state = 'waiting_approval'

    def action_approve(self):
        for record in self:
            if record.state != 'waiting_approval':
                raise UserError(_('Solo se pueden aprobar órdenes en espera de aprobación.'))
            record.state = 'approved'

    # Cálculos
    @api.depends('refaction_line_ids.total_price', 'labor_hours', 'labor_price')
    def _compute_totals(self):
        for record in self:
            lines_total = sum(record.refaction_line_ids.mapped('total_price'))
            record.labor_total = record.labor_hours * record.labor_price
            record.total_amount = lines_total + record.labor_total
PYFILE001

echo "✅ Archivo 1/4 creado: inmoser_service_order.py"

# =====================================================================
# ARCHIVO 2: inmoser_service_equipment.py (66 líneas)
# =====================================================================
cat > models/inmoser_service_equipment.py << 'PYFILE002'
# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import UserError
import logging

_logger = logging.getLogger(__name__)

try:
    import qrcode
    import base64
    from io import BytesIO
except ImportError:
    qrcode = None
    base64 = None
    BytesIO = None

class InmoserServiceEquipment(models.Model):
    _name = 'inmoser.service.equipment'
    _description = 'Equipo de Servicio Inmoser'
    _order = 'name'
    
    name = fields.Char(
        string='Referencia Equipo', required=True, index=True,
        copy=False, default=lambda self: _('New')
    )
    equipment_type = fields.Char(string='Tipo de Equipo', required=True)
    brand = fields.Char(string='Marca', required=True)
    model = fields.Char(string='Modelo')
    serial_number = fields.Char(string='Número de Serie')
    location = fields.Char(string='Ubicación')
    partner_id = fields.Many2one(
        'res.partner', string='Cliente', required=True,
        ondelete='restrict'
    )
    purchase_date = fields.Date(string='Fecha de Compra')
    warranty_end_date = fields.Date(string='Fin de Garantía')
    
    qr_code = fields.Binary(string='Código QR')
    qr_code_text = fields.Char(
        string='Texto QR', compute='_compute_qr_code_text', store=True
    )
    
    # Secuencia
    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name', _('New')) == _('New'):
                vals['name'] = self.env['ir.sequence'].next_by_code('inmoser.service.equipment') or _('New')
        return super().create(vals_list)
    
    @api.depends('name', 'serial_number')
    def _compute_qr_code_text(self):
        for equipment in self:
            equipment.qr_code_text = f"EQUIPO:{equipment.name}|SN:{equipment.serial_number or 'N/A'}"
    
    def action_generate_qr(self):
        if not qrcode:
            raise UserError(_(
                "La librería qrcode no está instalada. Ejecute: pip install qrcode[pil]"
            ))
        for equipment in self:
            qr_data = equipment.qr_code_text
            qr_image = qrcode.make(qr_data)
            buffered = BytesIO()
            qr_image.save(buffered, format="PNG")
            equipment.qr_code = base64.b64encode(buffered.getvalue())
PYFILE002

echo "✅ Archivo 2/4 creado: inmoser_service_equipment.py"

# =====================================================================
# ARCHIVO 3: inmoser_service_order_refaction_line.py (36 líneas)
# =====================================================================
cat > models/inmoser_service_order_refaction_line.py << 'PYFILE003'
# -*- coding: utf-8 -*-
from odoo import models, fields, api, _

class InmoserServiceOrderRefactionLine(models.Model):
    _name = 'inmoser.service.order.refaction.line'
    _description = 'Línea de Refacción de Orden de Servicio'
    
    order_id = fields.Many2one(
        'inmoser.service.order', string='Orden de Servicio',
        required=True, ondelete='cascade'
    )
    product_id = fields.Many2one(
        'product.product', string='Producto', required=True
    )
    quantity = fields.Float(string='Cantidad', default=1.0, digits='Product Unit of Measure')
    unit_price = fields.Monetary(string='Precio Unitario', currency_field='currency_id')
    total_price = fields.Monetary(
        string='Total', currency_field='currency_id',
        compute='_compute_total_price', store=True
    )
    currency_id = fields.Many2one(
        'res.currency', string='Currency',
        related='order_id.currency_id', readonly=True
    )
    description = fields.Text(string='Descripción')
    
    @api.depends('quantity', 'unit_price')
    def _compute_total_price(self):
        for line in self:
            line.total_price = line.quantity * line.unit_price
    
    @api.onchange('product_id')
    def _onchange_product_id(self):
        if self.product_id:
            self.unit_price = self.product_id.lst_price
            self.description = self.product_id.name
PYFILE003

echo "✅ Archivo 3/4 creado: inmoser_service_order_refaction_line.py"

# =====================================================================
# ARCHIVO 4: inmoser_service_type.py (17 líneas)
# =====================================================================
cat > models/inmoser_service_type.py << 'PYFILE004'
# -*- coding: utf-8 -*-
from odoo import models, fields

class InmoserServiceType(models.Model):
    _name = 'inmoser.service.type'
    _description = 'Tipo de Servicio Inmoser'
    _order = 'sequence'
    
    name = fields.Char(string='Nombre', required=True, translate=True)
    code = fields.Char(string='Código', required=True, copy=False)
    description = fields.Text(string='Descripción')
    sequence = fields.Integer(string='Secuencia', default=10)
    active = fields.Boolean(string='Activo', default=True)
    
    _sql_constraints = [
        ('code_uniq', 'unique(code)', 'El código del tipo de servicio debe ser único!'),
    ]
PYFILE004

echo "✅ Archivo 4/4 creado: inmoser_service_type.py"

# =====================================================================
# VERIFICACIÓN
# =====================================================================
echo ""
echo "📊 VERIFICANDO ARCHIVOS..."
wc -l models/inmoser_service_order.py
wc -l models/inmoser_service_equipment.py
wc -l models/inmoser_service_order_refaction_line.py
wc -l models/inmoser_service_type.py

echo ""
echo "🔍 COMPILANDO PARA VERIFICAR SINTAXIS..."
python3 -m py_compile models/*.py && echo "✅ SINTAXIS OK" || echo "❌ ERROR DE SINTAXIS"

echo ""
echo "🎉 ARCHIVOS CREADOS EXITOSAMENTE"
echo "Ahora ejecuta: bash fix_inmoser_files.sh"
