# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
from datetime import datetime, timedelta

class ServiceReprogramWizard(models.TransientModel):
    """
    Wizard para reagendar órdenes de servicio
    """
    _name = 'inmoser.service.reprogram.wizard'
    _description = 'Service Order Reprogramming Wizard'
    
    service_order_id = fields.Many2one(
        'inmoser.service.order',
        string='Service Order',
        required=True,
        readonly=True
    )
    
    current_date = fields.Datetime(
        string='Current Scheduled Date',
        readonly=True
    )
    
    new_date = fields.Datetime(
        string='New Scheduled Date',
        required=True,
        default=lambda self: fields.Datetime.now() + timedelta(days=1)
    )
    
    new_technician_id = fields.Many2one(
        'hr.employee',
        string='New Technician',
        domain=[('x_inmoser_is_technician', '=', True)]
    )
    
    keep_current_technician = fields.Boolean(
        string='Keep Current Technician',
        default=True
    )
    
    reason = fields.Text(
        string='Reason for Rescheduling',
        required=True
    )
    
    available_technicians = fields.Many2many(
        'hr.employee',
        string='Available Technicians',
        compute='_compute_available_technicians',
        readonly=True
    )
    
    notify_customer = fields.Boolean(
        string='Notify Customer',
        default=True
    )
    
    notify_technician = fields.Boolean(
        string='Notify Technician',
        default=True
    )
    
    @api.depends('new_date')
    def _compute_available_technicians(self):
        """Calcular técnicos disponibles para la nueva fecha"""
        for wizard in self:
            if wizard.new_date:
                available_techs = wizard._get_available_technicians(wizard.new_date)
                wizard.available_technicians = [(6, 0, available_techs.ids)]
            else:
                wizard.available_technicians = [(6, 0, [])]
    
    def _get_available_technicians(self, target_date):
        """Obtener técnicos disponibles para una fecha específica"""
        technicians = self.env['hr.employee'].search([
            ('x_inmoser_is_technician', '=', True),
            ('active', '=', True)
        ])
        
        available = self.env['hr.employee']
        
        for technician in technicians:
            if self.service_order_id._is_technician_available(technician, target_date):
                available |= technician
        
        return available
    
    @api.onchange('new_date')
    def _onchange_new_date(self):
        """Validar nueva fecha y sugerir técnico"""
        if self.new_date:
            # Validar que la fecha no sea en el pasado
            if self.new_date < fields.Datetime.now():
                return {
                    'warning': {
                        'title': _('Invalid Date'),
                        'message': _('The new date cannot be in the past.')
                    }
                }
            
            # Si se mantiene el técnico actual, verificar disponibilidad
            if self.keep_current_technician and self.service_order_id.assigned_technician_id:
                current_tech = self.service_order_id.assigned_technician_id
                if not self.service_order_id._is_technician_available(current_tech, self.new_date):
                    self.keep_current_technician = False
                    return {
                        'warning': {
                            'title': _('Technician Not Available'),
                            'message': _('The current technician is not available on the selected date. Please choose a different technician.')
                        }
                    }
    
    @api.onchange('keep_current_technician')
    def _onchange_keep_current_technician(self):
        """Manejar cambio de técnico"""
        if self.keep_current_technician:
            self.new_technician_id = False
        else:
            # Sugerir primer técnico disponible
            if self.available_technicians:
                self.new_technician_id = self.available_technicians[0]
    
    def action_reschedule(self):
        """Ejecutar el reagendamiento"""
        self.ensure_one()
        
        # Validaciones
        self._validate_reschedule_data()
        
        # Determinar técnico final
        final_technician = self._get_final_technician()
        
        # Actualizar la orden de servicio
        old_date = self.service_order_id.scheduled_date
        old_technician = self.service_order_id.assigned_technician_id
        
        self.service_order_id.write({
            'scheduled_date': self.new_date,
            'assigned_technician_id': final_technician.id,
        })
        
        # Registrar el cambio en el chatter
        self._log_reschedule_change(old_date, old_technician, final_technician)
        
        # Enviar notificaciones
        if self.notify_customer:
            self._send_customer_notification()
        
        if self.notify_technician:
            self._send_technician_notification(final_technician)
        
        # Crear actividades de seguimiento
        self._create_follow_up_activities(final_technician)
        
        return {
            'type': 'ir.actions.act_window_close'
        }
    
    def _validate_reschedule_data(self):
        """Validar datos del reagendamiento"""
        # Validar fecha
        if self.new_date < fields.Datetime.now():
            raise UserError(_('The new date cannot be in the past.'))
        
        # Validar técnico
        final_technician = self._get_final_technician()
        if not self.service_order_id._is_technician_available(final_technician, self.new_date):
            raise UserError(
                _('Technician %s is not available on %s') % (
                    final_technician.name, self.new_date
                )
            )
        
        # Validar razón
        if not self.reason.strip():
            raise UserError(_('Reason for rescheduling is required.'))
    
    def _get_final_technician(self):
        """Obtener el técnico final para la reagendación"""
        if self.keep_current_technician:
            return self.service_order_id.assigned_technician_id
        else:
            if not self.new_technician_id:
                raise UserError(_('Please select a technician for the new date.'))
            return self.new_technician_id
    
    def _log_reschedule_change(self, old_date, old_technician, new_technician):
        """Registrar el cambio en el chatter"""
        message_parts = []
        
        # Cambio de fecha
        message_parts.append(
            _('Scheduled date changed from %s to %s') % (
                old_date.strftime('%Y-%m-%d %H:%M') if old_date else _('Not set'),
                self.new_date.strftime('%Y-%m-%d %H:%M')
            )
        )
        
        # Cambio de técnico
        if old_technician != new_technician:
            message_parts.append(
                _('Technician changed from %s to %s') % (
                    old_technician.name if old_technician else _('Not assigned'),
                    new_technician.name
                )
            )
        
        # Razón
        message_parts.append(_('Reason: %s') % self.reason)
        
        self.service_order_id.message_post(
            body='<br/>'.join(message_parts),
            message_type='notification',
            subtype_xmlid='mail.mt_note'
        )
    
    def _send_customer_notification(self):
        """Enviar notificación al cliente"""
        template = self.env.ref(
            'inmoser_service_order.email_template_service_rescheduled',
            raise_if_not_found=False
        )
        
        if template:
            # Preparar contexto para el template
            ctx = {
                'old_date': self.current_date,
                'new_date': self.new_date,
                'reason': self.reason,
                'technician': self._get_final_technician().name
            }
            
            template.with_context(ctx).send_mail(
                self.service_order_id.id,
                force_send=True
            )
    
    def _send_technician_notification(self, technician):
        """Enviar notificación al técnico"""
        if technician.user_id:
            # Crear actividad para el técnico
            self.service_order_id.activity_schedule(
                'mail.mail_activity_data_todo',
                user_id=technician.user_id.id,
                summary=_('Service Order Rescheduled: %s') % self.service_order_id.name,
                note=_('Service order %s has been rescheduled to %s. Reason: %s') % (
                    self.service_order_id.name,
                    self.new_date.strftime('%Y-%m-%d %H:%M'),
                    self.reason
                )
            )
    
    def _create_follow_up_activities(self, technician):
        """Crear actividades de seguimiento"""
        # Actividad de recordatorio 1 día antes
        reminder_date = self.new_date - timedelta(days=1)
        
        if reminder_date > fields.Datetime.now() and technician.user_id:
            self.service_order_id.activity_schedule(
                'mail.mail_activity_data_call',
                date_deadline=reminder_date.date(),
                user_id=technician.user_id.id,
                summary=_('Service Reminder: %s') % self.service_order_id.name,
                note=_('Reminder: You have a service scheduled for tomorrow at %s') % (
                    self.new_date.strftime('%H:%M')
                )
            )
    
    def action_cancel(self):
        """Cancelar el reagendamiento"""
        return {'type': 'ir.actions.act_window_close'}
    
    @api.model
    def default_get(self, fields_list):
        """Establecer valores por defecto"""
        res = super().default_get(fields_list)
        
        # Obtener orden de servicio del contexto
        service_order_id = self.env.context.get('default_service_order_id')
        if service_order_id:
            service_order = self.env['inmoser.service.order'].browse(service_order_id)
            res.update({
                'service_order_id': service_order_id,
                'current_date': service_order.scheduled_date,
            })
        
        return res

