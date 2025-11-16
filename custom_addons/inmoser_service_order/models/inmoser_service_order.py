from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
from datetime import datetime

class InmoserServiceOrder(models.Model):
    _name = 'inmoser.service.order'
    _description = 'Inmoser Service Order'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'name desc'

    name = fields.Char(
        string='Order Number',
        required=True,
        copy=False,
        readonly=True,
        default=lambda self: _('New')
    )
    partner_id = fields.Many2one(
        'res.partner',
        string='Customer',
        required=True,
        tracking=True
    )
    equipment_id = fields.Many2one(
        'inmoser.service.equipment',
        string='Equipment',
        required=True,
        tracking=True
    )
    service_type_id = fields.Many2one(
        'inmoser.service.type',
        string='Service Type',
        required=True,
        tracking=True
    )
    date_scheduled = fields.Datetime(
        string='Scheduled Date',
        required=True,
        default=fields.Datetime.now,
        tracking=True
    )
    assigned_technician_id = fields.Many2one(
        'hr.employee',
        string='Assigned Technician',
        domain="[('x_inmoser_is_technician', '=', True)]",
        tracking=True
    )
    state = fields.Selection([
        ('draft', 'Draft'),
        ('confirmed', 'Confirmed'),
        ('assigned', 'Assigned'),
        ('in_progress', 'In Progress'),
        ('pending_approval', 'Pending Approval'),
        ('approved', 'Approved'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled')
    ], string='Status', default='draft', required=True, tracking=True)
    
    service_order_line_ids = fields.One2many(
        'inmoser.service.order.refaction.line',
        'order_id',
        string='Refaction Lines'
    )
    total_amount = fields.Monetary(
        string='Total Amount',
        compute='_compute_total_amount',
        store=True,
        currency_field='currency_id'
    )
    currency_id = fields.Many2one(
        'res.currency',
        string='Currency',
        default=lambda self: self.env.company.currency_id
    )
    date_start = fields.Datetime(
        string='Start Date',
        readonly=True,
        tracking=True
    )
    date_end = fields.Datetime(
        string='End Date',
        readonly=True,
        tracking=True
    )
    labor_hours = fields.Float(
        string='Labor Hours',
        digits=(5, 2)
    )
    labor_price = fields.Monetary(
        string='Labor Price',
        currency_field='currency_id'
    )
    labor_total = fields.Monetary(
        string='Labor Total',
        compute='_compute_labor_total',
        store=True,
        currency_field='currency_id'
    )
    diagnosis = fields.Text(
        string='Diagnosis'
    )
    work_performed = fields.Text(
        string='Work Performed'
    )
    invoice_id = fields.Many2one(
        'account.move',
        string='Invoice',
        readonly=True,
        copy=False
    )

    @api.model
    def create(self, vals):
        if vals.get('name', _('New')) == _('New'):
            vals['name'] = self.env['ir.sequence'].next_by_code('inmoser.service.order') or _('New')
        return super(InmoserServiceOrder, self).create(vals)

    @api.depends('service_order_line_ids.price_subtotal', 'labor_total')
    def _compute_total_amount(self):
        for order in self:
            refactions_total = sum(order.service_order_line_ids.mapped('price_subtotal'))
            order.total_amount = refactions_total + order.labor_total

    @api.depends('labor_hours', 'labor_price')
    def _compute_labor_total(self):
        for order in self:
            order.labor_total = order.labor_hours * order.labor_price

    # ═══════════════════════════════════════════════════════════
    # MÉTODOS DE TRANSICIÓN DE ESTADO
    # ═══════════════════════════════════════════════════════════
    
    def action_confirm(self):
        """Confirmar la orden de servicio"""
        for order in self:
            if order.state != 'draft':
                raise UserError(_('Only draft orders can be confirmed.'))
            order.write({
                'state': 'confirmed'
            })
            order.message_post(body=_('Service order confirmed.'))
        return True

    def action_assign(self):
        """Asignar técnico a la orden"""
        for order in self:
            if order.state not in ['confirmed', 'draft']:
                raise UserError(_('Order must be confirmed before assigning.'))
            if not order.assigned_technician_id:
                raise UserError(_('Please assign a technician before proceeding.'))
            order.write({
                'state': 'assigned'
            })
            order.message_post(
                body=_('Service order assigned to %s.') % order.assigned_technician_id.name
            )
        return True

    def action_start(self):
        """Iniciar trabajo en la orden"""
        for order in self:
            if order.state != 'assigned':
                raise UserError(_('Order must be assigned before starting.'))
            if not order.assigned_technician_id:
                raise UserError(_('A technician must be assigned to start the work.'))
            order.write({
                'state': 'in_progress',
                'date_start': fields.Datetime.now()
            })
            order.message_post(body=_('Service work started.'))
        return True

    def action_request_approval(self):
        """Solicitar aprobación del cliente"""
        for order in self:
            if order.state != 'in_progress':
                raise UserError(_('Work must be in progress to request approval.'))
            if not order.diagnosis:
                raise UserError(_('Please provide a diagnosis before requesting approval.'))
            order.write({
                'state': 'pending_approval'
            })
            order.message_post(body=_('Approval requested from customer.'))
            # Aquí se puede enviar email al cliente
            if order.partner_id.email:
                order._send_approval_email()
        return True

    def action_approve(self):
        """Aprobar el servicio (por el cliente o manager)"""
        for order in self:
            if order.state != 'pending_approval':
                raise UserError(_('Order must be pending approval.'))
            order.write({
                'state': 'approved'
            })
            order.message_post(body=_('Service approved by customer.'))
        return True

    def action_complete(self):
        """Completar la orden de servicio"""
        for order in self:
            if order.state not in ['in_progress', 'approved']:
                raise UserError(_('Order must be in progress or approved to complete.'))
            if not order.work_performed:
                raise UserError(_('Please describe the work performed before completing.'))
            order.write({
                'state': 'completed',
                'date_end': fields.Datetime.now()
            })
            order.message_post(body=_('Service order completed.'))
            # Crear factura automáticamente si es necesario
            # order._create_invoice()
        return True

    def action_cancel(self):
        """Cancelar la orden de servicio"""
        for order in self:
            if order.state == 'completed':
                raise UserError(_('Cannot cancel a completed order.'))
            if order.invoice_id and order.invoice_id.state == 'posted':
                raise UserError(_('Cannot cancel an order with a posted invoice.'))
            order.write({
                'state': 'cancelled'
            })
            order.message_post(body=_('Service order cancelled.'))
        return True

    def action_reset_to_draft(self):
        """Regresar a borrador"""
        for order in self:
            if order.invoice_id:
                raise UserError(_('Cannot reset an order with an invoice.'))
            order.write({
                'state': 'draft',
                'date_start': False,
                'date_end': False
            })
            order.message_post(body=_('Service order reset to draft.'))
        return True

    # ═══════════════════════════════════════════════════════════
    # MÉTODOS AUXILIARES
    # ═══════════════════════════════════════════════════════════

    def _send_approval_email(self):
        """Enviar email de solicitud de aprobación al cliente"""
        self.ensure_one()
        template = self.env.ref('inmoser_service_order.email_template_customer_approval', False)
        if template:
            template.send_mail(self.id, force_send=True)

    def _create_invoice(self):
        """Crear factura desde la orden de servicio"""
        self.ensure_one()
        
        if self.invoice_id:
            raise UserError(_('An invoice already exists for this order.'))
        
        invoice_lines = []
        
        # Agregar líneas de refacciones
        for line in self.service_order_line_ids:
            invoice_lines.append((0, 0, {
                'product_id': line.product_id.id,
                'name': line.name,
                'quantity': line.quantity,
                'price_unit': line.price_unit,
            }))
        
        # Agregar línea de mano de obra si existe
        if self.labor_hours > 0:
            labor_product = self.env.ref('inmoser_service_order.product_labor_service', False)
            if labor_product:
                invoice_lines.append((0, 0, {
                    'product_id': labor_product.id,
                    'name': _('Labor: %s hours') % self.labor_hours,
                    'quantity': self.labor_hours,
                    'price_unit': self.labor_price,
                }))
        
        # Crear factura
        invoice_vals = {
            'partner_id': self.partner_id.id,
            'move_type': 'out_invoice',
            'invoice_line_ids': invoice_lines,
            'service_order_id': self.id,
        }
        
        invoice = self.env['account.move'].create(invoice_vals)
        self.write({'invoice_id': invoice.id})
        
        return invoice

    def action_create_invoice(self):
        """Acción para crear factura manualmente"""
        self.ensure_one()
        if self.state != 'completed':
            raise UserError(_('Order must be completed to create an invoice.'))
        invoice = self._create_invoice()
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'account.move',
            'res_id': invoice.id,
            'view_mode': 'form',
            'target': 'current',
        }

    @api.constrains('date_start', 'date_end')
    def _check_dates(self):
        """Validar que la fecha de fin sea posterior a la de inicio"""
        for order in self:
            if order.date_start and order.date_end:
                if order.date_end < order.date_start:
                    raise ValidationError(_('End date must be after start date.'))
