# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
import base64
import logging

_logger = logging.getLogger(__name__)

class ServiceCompleteWizard(models.TransientModel):
    """
    Wizard para completar servicios desde el calendario del técnico
    """
    _name = 'inmoser.service.complete.wizard'
    _description = 'Service Completion Wizard'
    
    service_order_id = fields.Many2one(
        'inmoser.service.order',
        string='Service Order',
        required=True,
        readonly=True
    )
    
    diagnosis = fields.Text(
        string='Diagnosis',
        required=True,
        help='Technical diagnosis of the equipment issue'
    )
    
    work_performed = fields.Text(
        string='Work Performed',
        required=True,
        help='Description of the work performed to fix the issue'
    )
    
    photo_before = fields.Binary(
        string='Photo Before Service',
        help='Photo taken before starting the service'
    )
    
    photo_after = fields.Binary(
        string='Photo After Service',
        help='Photo taken after completing the service'
    )
    
    requires_parts = fields.Boolean(
        string='Requires Parts/Refactions',
        default=False
    )
    
    refaction_line_ids = fields.One2many(
        'inmoser.service.complete.refaction.line',
        'wizard_id',
        string='Parts Used'
    )
    
    customer_signature = fields.Binary(
        string='Customer Signature',
        help='Digital signature of customer approval'
    )
    
    technician_notes = fields.Text(
        string='Technician Notes',
        help='Additional notes from the technician'
    )
    
    completion_time = fields.Datetime(
        string='Completion Time',
        default=fields.Datetime.now,
        required=True
    )
    
    customer_satisfaction = fields.Selection([
        ('1', 'Very Unsatisfied'),
        ('2', 'Unsatisfied'),
        ('3', 'Neutral'),
        ('4', 'Satisfied'),
        ('5', 'Very Satisfied')
    ], string='Customer Satisfaction', default='5')
    
    @api.onchange('requires_parts')
    def _onchange_requires_parts(self):
        """Limpiar líneas de refacciones si no se requieren"""
        if not self.requires_parts:
            self.refaction_line_ids = [(5, 0, 0)]
    
    def action_complete_service(self):
        """Completar el servicio"""
        self.ensure_one()
        
        # Validaciones
        self._validate_completion_data()
        
        # Actualizar la orden de servicio
        self._update_service_order()
        
        # Procesar refacciones si las hay
        if self.requires_parts and self.refaction_line_ids:
            self._process_refactions()
        
        # Enviar notificación al cliente
        self._send_completion_notification()
        
        # Crear actividades de seguimiento
        self._create_follow_up_activities()
        
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Service Completed'),
                'message': _('Service order %s has been completed successfully.') % self.service_order_id.name,
                'type': 'success',
                'sticky': False,
            }
        }
    
    def _validate_completion_data(self):
        """Validar datos de completación"""
        # Validar diagnóstico
        if not self.diagnosis.strip():
            raise UserError(_('Diagnosis is required to complete the service.'))
        
        # Validar trabajo realizado
        if not self.work_performed.strip():
            raise UserError(_('Work performed description is required.'))
        
        # Validar refacciones si se requieren
        if self.requires_parts and not self.refaction_line_ids:
            raise UserError(_('Please add the parts used or uncheck "Requires Parts".'))
        
        # Validar que el servicio esté en progreso
        if self.service_order_id.state != 'in_progress':
            raise UserError(_('Only services in progress can be completed.'))
        
        # Validar tiempo de completación
        if self.completion_time < self.service_order_id.start_date:
            raise UserError(_('Completion time cannot be before service start time.'))
    
    def _update_service_order(self):
        """Actualizar la orden de servicio"""
        vals = {
            'diagnosis': self.diagnosis,
            'work_performed': self.work_performed,
            'end_date': self.completion_time,
            'technician_notes': self.technician_notes,
            'customer_satisfaction': self.customer_satisfaction,
        }
        
        # Añadir fotos si existen
        if self.photo_before:
            vals['photo_before'] = self.photo_before
        
        if self.photo_after:
            vals['photo_after'] = self.photo_after
        
        # Añadir firma del cliente si existe
        if self.customer_signature:
            vals['customer_signature'] = self.customer_signature
        
        self.service_order_id.write(vals)
        
        # Cambiar estado a completado
        self.service_order_id.action_complete_service()
    
    def _process_refactions(self):
        """Procesar refacciones utilizadas"""
        for line in self.refaction_line_ids:
            # Crear línea de refacción en la orden
            refaction_vals = {
                'service_order_id': self.service_order_id.id,
                'product_id': line.product_id.id,
                'description': line.description,
                'quantity': line.quantity,
                'unit_price': line.unit_price,
            }
            
            self.env['inmoser.service.order.refaction.line'].create(refaction_vals)
            
            # Actualizar inventario virtual del técnico
            self._update_technician_inventory(line)
    
    def _update_technician_inventory(self, line):
        """Actualizar inventario virtual del técnico"""
        technician = self.service_order_id.assigned_technician_id
        
        if technician and hasattr(technician, 'x_inmoser_virtual_inventory_ids'):
            # Buscar el producto en el inventario virtual
            inventory_line = technician.x_inmoser_virtual_inventory_ids.filtered(
                lambda l: l.product_id == line.product_id
            )
            
            if inventory_line:
                # Reducir cantidad disponible
                new_quantity = inventory_line.available_quantity - line.quantity
                if new_quantity < 0:
                    _logger.warning(
                        f"Negative inventory for product {line.product_id.name} "
                        f"for technician {technician.name}"
                    )
                    new_quantity = 0
                
                inventory_line.available_quantity = new_quantity
    
    def _send_completion_notification(self):
        """Enviar notificación de completación al cliente"""
        template = self.env.ref(
            'inmoser_service_order.email_template_service_completed',
            raise_if_not_found=False
        )
        
        if template:
            template.send_mail(
                self.service_order_id.id,
                force_send=True
            )
    
    def _create_follow_up_activities(self):
        """Crear actividades de seguimiento"""
        # Actividad para call center: seguimiento de satisfacción
        call_center_users = self.env.ref('inmoser_service_order.group_inmoser_call_center').users
        
        if call_center_users:
            self.service_order_id.activity_schedule(
                'mail.mail_activity_data_call',
                user_id=call_center_users[0].id,
                summary=_('Customer Satisfaction Follow-up: %s') % self.service_order_id.name,
                note=_('Follow up with customer about service satisfaction. Rating: %s/5') % (
                    self.customer_satisfaction or 'Not rated'
                )
            )
    
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
                'diagnosis': service_order.diagnosis or '',
            })
        
        return res

class ServiceCompleteRefactionLine(models.TransientModel):
    """
    Líneas de refacciones para el wizard de completar servicio
    """
    _name = 'inmoser.service.complete.refaction.line'
    _description = 'Service Completion Refaction Line'
    
    wizard_id = fields.Many2one(
        'inmoser.service.complete.wizard',
        string='Wizard',
        required=True,
        ondelete='cascade'
    )
    
    product_id = fields.Many2one(
        'product.product',
        string='Product',
        required=True,
        domain=[('type', 'in', ['product', 'consu'])]
    )
    
    description = fields.Text(
        string='Description',
        help='Additional description of the part used'
    )
    
    quantity = fields.Float(
        string='Quantity',
        default=1.0,
        required=True
    )
    
    unit_price = fields.Float(
        string='Unit Price',
        required=True
    )
    
    total_price = fields.Float(
        string='Total Price',
        compute='_compute_total_price',
        store=True
    )
    
    @api.depends('quantity', 'unit_price')
    def _compute_total_price(self):
        """Calcular precio total"""
        for line in self:
            line.total_price = line.quantity * line.unit_price
    
    @api.onchange('product_id')
    def _onchange_product_id(self):
        """Actualizar precio al cambiar producto"""
        if self.product_id:
            self.unit_price = self.product_id.list_price
            self.description = self.product_id.name

