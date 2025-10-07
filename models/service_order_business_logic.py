# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
from datetime import datetime, timedelta
import logging

_logger = logging.getLogger(__name__)

class ServiceOrderBusinessLogic(models.Model):
    """
    Extensión del modelo de órdenes de servicio con lógica de negocio avanzada
    """
    _inherit = 'inmoser.service.order'
    
    # ==========================================
    # MÉTODOS DE TRANSICIÓN DE ESTADOS
    # ==========================================
    
    def action_assign_technician(self):
        """Asignar técnico a la orden de servicio"""
        for record in self:
            if record.state != 'draft':
                raise UserError(_('Only draft orders can be assigned to technicians.'))
            
            if not record.assigned_technician_id:
                # Buscar técnico disponible automáticamente
                available_technician = record._find_available_technician()
                if available_technician:
                    record.assigned_technician_id = available_technician
                else:
                    raise UserError(_('No available technicians found for the scheduled date and time.'))
            
            # Validar disponibilidad del técnico
            if not record._validate_technician_availability():
                raise UserError(_('The selected technician is not available at the scheduled time.'))
            
            record.state = 'assigned'
            record._send_assignment_notification()
            
            # Crear actividad para el técnico
            record.activity_schedule(
                'mail.mail_activity_data_todo',
                user_id=record.assigned_technician_id.user_id.id,
                summary=_('Service Order Assigned: %s') % record.name,
                note=_('You have been assigned to service order %s for customer %s. Equipment: %s') % (
                    record.name, record.partner_id.name, record.equipment_id.name
                )
            )
    
    def action_start_service(self):
        """Iniciar el servicio"""
        for record in self:
            if record.state != 'assigned':
                raise UserError(_('Only assigned orders can be started.'))
            
            if record.assigned_technician_id.user_id != self.env.user:
                raise UserError(_('Only the assigned technician can start this service.'))
            
            record.state = 'in_progress'
            record.start_date = fields.Datetime.now()
            record._send_service_started_notification()
    
    def action_request_approval(self):
        """Solicitar aprobación del cliente"""
        for record in self:
            if record.state != 'in_progress':
                raise UserError(_('Only services in progress can request approval.'))
            
            if not record.diagnosis:
                raise UserError(_('Diagnosis is required before requesting approval.'))
            
            if not record.refaction_line_ids and record.service_type_id.requires_approval:
                raise UserError(_('At least one refaction line is required for services that require approval.'))
            
            record.state = 'pending_approval'
            record._calculate_total_amount()
            record._send_approval_request_notification()
    
    def action_customer_accept(self):
        """Cliente acepta el servicio"""
        for record in self:
            if record.state != 'pending_approval':
                raise UserError(_('Only orders pending approval can be accepted.'))
            
            record.state = 'accepted'
            record.acceptance_status = 'accepted'
            record._send_acceptance_notification()
            
            # Verificar disponibilidad de refacciones
            if not record._check_refaction_availability():
                # Si no hay refacciones disponibles, reagendar
                record._auto_reschedule_for_parts()
    
    def action_customer_reject(self):
        """Cliente rechaza el servicio"""
        for record in self:
            if record.state != 'pending_approval':
                raise UserError(_('Only orders pending approval can be rejected.'))
            
            if not record.rejection_reason:
                raise UserError(_('Rejection reason is required.'))
            
            record.state = 'rejected'
            record.acceptance_status = 'rejected'
            record._send_rejection_notification()
    
    def action_complete_service(self):
        """Completar el servicio"""
        for record in self:
            if record.state != 'accepted':
                raise UserError(_('Only accepted orders can be completed.'))
            
            if record.assigned_technician_id.user_id != self.env.user:
                raise UserError(_('Only the assigned technician can complete this service.'))
            
            if not record.work_performed:
                raise UserError(_('Work performed description is required.'))
            
            if record.service_type_id.allow_photos and not record.photo_after:
                raise UserError(_('After service photo is required for this service type.'))
            
            record.state = 'done'
            record.end_date = fields.Datetime.now()
            record._calculate_duration()
            record._consume_refactions()
            record._send_completion_notification()
    
    def action_reschedule(self):
        """Reagendar el servicio"""
        for record in self:
            if record.state in ['done', 'cancelled']:
                raise UserError(_('Completed or cancelled orders cannot be rescheduled.'))
            
            # Abrir wizard de reagendamiento
            return {
                'type': 'ir.actions.act_window',
                'name': _('Reschedule Service Order'),
                'res_model': 'inmoser.service.reprogram.wizard',
                'view_mode': 'form',
                'target': 'new',
                'context': {
                    'default_service_order_id': record.id,
                    'default_current_date': record.scheduled_date,
                }
            }
    
    def action_cancel(self):
        """Cancelar el servicio"""
        for record in self:
            if record.state == 'done':
                raise UserError(_('Completed orders cannot be cancelled.'))
            
            record.state = 'cancelled'
            record._send_cancellation_notification()
            
            # Liberar refacciones reservadas
            record._release_reserved_refactions()
    
    # ==========================================
    # MÉTODOS DE LÓGICA DE NEGOCIO
    # ==========================================
    
    def _find_available_technician(self):
        """Encontrar técnico disponible para la fecha programada"""
        if not self.scheduled_date:
            return False
        
        # Buscar técnicos activos
        technicians = self.env['hr.employee'].search([
            ('x_inmoser_is_technician', '=', True),
            ('active', '=', True)
        ])
        
        for technician in technicians:
            if self._is_technician_available(technician, self.scheduled_date):
                return technician
        
        return False
    
    def _is_technician_available(self, technician, scheduled_date):
        """Verificar si un técnico está disponible en una fecha específica"""
        if not scheduled_date or not technician:
            return False
        
        # Verificar horarios disponibles del técnico
        if not self._check_technician_schedule(technician, scheduled_date):
            return False
        
        # Verificar órdenes existentes del técnico
        existing_orders = self.search([
            ('assigned_technician_id', '=', technician.id),
            ('scheduled_date', '=', scheduled_date),
            ('state', 'not in', ['done', 'cancelled'])
        ])
        
        # Verificar límite diario de órdenes
        daily_orders = self.search_count([
            ('assigned_technician_id', '=', technician.id),
            ('scheduled_date', '>=', scheduled_date.replace(hour=0, minute=0, second=0)),
            ('scheduled_date', '<=', scheduled_date.replace(hour=23, minute=59, second=59)),
            ('state', 'not in', ['done', 'cancelled'])
        ])
        
        max_daily = technician.x_inmoser_max_daily_orders or 8
        
        return len(existing_orders) == 0 and daily_orders < max_daily
    
    def _check_technician_schedule(self, technician, scheduled_date):
        """Verificar si la fecha está dentro del horario del técnico"""
        if not technician.x_inmoser_available_hours:
            return True  # Sin restricciones de horario
        
        # Parsear horarios disponibles (formato: "10-12,12-14,15-17")
        available_hours = technician.x_inmoser_available_hours.split(',')
        scheduled_hour = scheduled_date.hour
        
        for time_slot in available_hours:
            if '-' in time_slot:
                start_hour, end_hour = map(int, time_slot.strip().split('-'))
                if start_hour <= scheduled_hour < end_hour:
                    return True
        
        return False
    
    def _validate_technician_availability(self):
        """Validar disponibilidad del técnico asignado"""
        if not self.assigned_technician_id or not self.scheduled_date:
            return True
        
        return self._is_technician_available(self.assigned_technician_id, self.scheduled_date)
    
    def _calculate_total_amount(self):
        """Calcular el monto total de la orden"""
        for record in self:
            total = record.service_type_id.base_price or 0.0
            
            for line in record.refaction_line_ids:
                total += line.total_price
            
            record.total_amount = total
    
    def _calculate_duration(self):
        """Calcular la duración del servicio"""
        for record in self:
            if record.start_date and record.end_date:
                duration = record.end_date - record.start_date
                record.duration = duration.total_seconds() / 3600.0  # Convertir a horas
    
    def _check_refaction_availability(self):
        """Verificar disponibilidad de refacciones en el almacén virtual del técnico"""
        if not self.assigned_technician_id.x_inmoser_virtual_warehouse_id:
            return True  # Sin control de inventario
        
        warehouse = self.assigned_technician_id.x_inmoser_virtual_warehouse_id
        
        for line in self.refaction_line_ids:
            # Buscar stock disponible
            stock_quant = self.env['stock.quant'].search([
                ('product_id', '=', line.product_id.id),
                ('location_id', '=', warehouse.lot_stock_id.id),
                ('quantity', '>', 0)
            ], limit=1)
            
            if not stock_quant or stock_quant.quantity < line.quantity:
                line.available_qty = stock_quant.quantity if stock_quant else 0
                return False
            else:
                line.available_qty = stock_quant.quantity
        
        return True
    
    def _consume_refactions(self):
        """Consumir refacciones del almacén virtual"""
        if not self.assigned_technician_id.x_inmoser_virtual_warehouse_id:
            return
        
        warehouse = self.assigned_technician_id.x_inmoser_virtual_warehouse_id
        
        for line in self.refaction_line_ids:
            # Crear movimiento de stock
            self.env['stock.move'].create({
                'name': _('Service Order %s - %s') % (self.name, line.product_id.name),
                'product_id': line.product_id.id,
                'product_uom_qty': line.quantity,
                'product_uom': line.product_uom_id.id,
                'location_id': warehouse.lot_stock_id.id,
                'location_dest_id': self.env.ref('stock.stock_location_customers').id,
                'origin': self.name,
                'state': 'done',
            })
    
    def _release_reserved_refactions(self):
        """Liberar refacciones reservadas (en caso de cancelación)"""
        # Implementar lógica de liberación de reservas si es necesario
        pass
    
    def _auto_reschedule_for_parts(self):
        """Reagendar automáticamente por falta de refacciones"""
        # Buscar próxima fecha disponible (ejemplo: +3 días)
        new_date = self.scheduled_date + timedelta(days=3)
        
        # Buscar técnico disponible en la nueva fecha
        available_technician = self._find_available_technician_for_date(new_date)
        
        if available_technician:
            self.scheduled_date = new_date
            self.assigned_technician_id = available_technician
            self.state = 'assigned'
            
            # Notificar reagendamiento
            self.message_post(
                body=_('Service automatically rescheduled to %s due to parts availability.') % new_date,
                message_type='notification'
            )
    
    def _find_available_technician_for_date(self, target_date):
        """Encontrar técnico disponible para una fecha específica"""
        technicians = self.env['hr.employee'].search([
            ('x_inmoser_is_technician', '=', True),
            ('active', '=', True)
        ])
        
        for technician in technicians:
            if self._is_technician_available(technician, target_date):
                return technician
        
        return False
    
    # ==========================================
    # MÉTODOS DE NOTIFICACIONES
    # ==========================================
    
    def _send_assignment_notification(self):
        """Enviar notificación de asignación"""
        template = self.env.ref('inmoser_service_order.email_template_service_assigned', raise_if_not_found=False)
        if template:
            template.send_mail(self.id, force_send=True)
    
    def _send_service_started_notification(self):
        """Enviar notificación de inicio de servicio"""
        self.message_post(
            body=_('Service started by technician %s') % self.assigned_technician_id.name,
            message_type='notification'
        )
    
    def _send_approval_request_notification(self):
        """Enviar notificación de solicitud de aprobación"""
        template = self.env.ref('inmoser_service_order.email_template_approval_request', raise_if_not_found=False)
        if template:
            template.send_mail(self.id, force_send=True)
    
    def _send_acceptance_notification(self):
        """Enviar notificación de aceptación"""
        self.message_post(
            body=_('Service approved by customer'),
            message_type='notification'
        )
    
    def _send_rejection_notification(self):
        """Enviar notificación de rechazo"""
        self.message_post(
            body=_('Service rejected by customer. Reason: %s') % self.rejection_reason,
            message_type='notification'
        )
    
    def _send_completion_notification(self):
        """Enviar notificación de finalización"""
        template = self.env.ref('inmoser_service_order.email_template_service_completed', raise_if_not_found=False)
        if template:
            template.send_mail(self.id, force_send=True)
    
    def _send_cancellation_notification(self):
        """Enviar notificación de cancelación"""
        self.message_post(
            body=_('Service order cancelled'),
            message_type='notification'
        )
    
    # ==========================================
    # VALIDACIONES
    # ==========================================
    
    @api.constrains('scheduled_date', 'assigned_technician_id')
    def _check_technician_availability_constraint(self):
        """Validar disponibilidad del técnico al guardar"""
        for record in self:
            if record.assigned_technician_id and record.scheduled_date:
                if not record._validate_technician_availability():
                    raise ValidationError(
                        _('Technician %s is not available on %s') % (
                            record.assigned_technician_id.name,
                            record.scheduled_date
                        )
                    )
    
    @api.constrains('refaction_line_ids')
    def _check_refaction_lines(self):
        """Validar líneas de refacciones"""
        for record in self:
            if record.service_type_id.requires_approval and record.state == 'pending_approval':
                if not record.refaction_line_ids:
                    raise ValidationError(
                        _('At least one refaction line is required for service type %s') % 
                        record.service_type_id.name
                    )
    
    # ==========================================
    # MÉTODOS AUTOMÁTICOS
    # ==========================================
    
    @api.model
    def _cron_check_overdue_orders(self):
        """Cron job para marcar órdenes vencidas"""
        overdue_orders = self.search([
            ('scheduled_date', '<', fields.Datetime.now()),
            ('state', 'in', ['draft', 'assigned']),
            ('is_overdue', '=', False)
        ])
        
        for order in overdue_orders:
            order.is_overdue = True
            order.message_post(
                body=_('Service order is now overdue'),
                message_type='notification'
            )
    
    @api.model
    def _cron_send_daily_reminders(self):
        """Cron job para enviar recordatorios diarios"""
        tomorrow = fields.Date.today() + timedelta(days=1)
        
        # Recordatorios para técnicos
        orders_tomorrow = self.search([
            ('scheduled_date', '>=', tomorrow),
            ('scheduled_date', '<', tomorrow + timedelta(days=1)),
            ('state', '=', 'assigned')
        ])
        
        for order in orders_tomorrow:
            order.activity_schedule(
                'mail.mail_activity_data_todo',
                user_id=order.assigned_technician_id.user_id.id,
                summary=_('Service Order Tomorrow: %s') % order.name,
                note=_('You have a service scheduled for tomorrow: %s at %s') % (
                    order.partner_id.name, order.scheduled_date
                )
            )

