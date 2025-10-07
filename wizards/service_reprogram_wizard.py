from odoo import models, fields, api, _
from odoo.exceptions import ValidationError

class ServiceReprogramWizard(models.TransientModel):
    _name = 'service.reprogram.wizard'
    _description = 'Wizard para Reprogramar Servicio'
    
    service_order_id = fields.Many2one('service.order', string="Orden de Servicio", required=True)
    new_date = fields.Datetime(string="Nueva Fecha", required=True)
    new_technician_id = fields.Many2one('hr.employee', string="Nuevo Técnico", 
                                        domain="[('is_technician', '=', True)]")
    reason = fields.Text(string="Motivo de Reprogramación", required=True)
    
    @api.model
    def default_get(self, fields):
        res = super(ServiceReprogramWizard, self).default_get(fields)
        if self.env.context.get('active_id') and self.env.context.get('active_model') == 'service.order':
            service_order = self.env['service.order'].browse(self.env.context['active_id'])
            res['service_order_id'] = service_order.id
            res['new_date'] = service_order.scheduled_date
            res['new_technician_id'] = service_order.technician_id.id
        return res
    
    def action_reprogram_service(self):
        self.ensure_one()
        service_order = self.service_order_id
        
        # Validar que la nueva fecha sea futura
        if self.new_date < fields.Datetime.now():
            raise ValidationError(_("La nueva fecha debe ser futura"))
        
        # Validar disponibilidad del técnico si se cambia
        if self.new_technician_id and self.new_technician_id != service_order.technician_id:
            # Verificar si el técnico tiene servicios en la misma fecha
            conflicting_services = self.env['service.order'].search([
                ('technician_id', '=', self.new_technician_id.id),
                ('scheduled_date', '=', self.new_date),
                ('state', 'not in', ['done', 'cancel']),
                ('id', '!=', service_order.id)
            ])
            if conflicting_services:
                raise ValidationError(_(
                    "El técnico %s ya tiene un servicio programado para esta fecha"
                ) % self.new_technician_id.name)
        
        # Actualizar orden de servicio
        service_order.write({
            'scheduled_date': self.new_date,
            'technician_id': self.new_technician_id.id if self.new_technician_id else service_order.technician_id.id,
        })
        
        # Enviar notificación
        template = self.env.ref('inmoser_service_order.service_confirmation_email_template')
        if template:
            template.send_mail(service_order.id)
        
        return {'type': 'ir.actions.act_window_close'}
