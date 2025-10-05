# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
from datetime import datetime, timedelta
import logging

_logger = logging.getLogger(__name__)

class HrEmployeeServiceIntegration(models.Model):
    """
    Extensión del modelo de empleados para integración con servicios
    """
    _inherit = 'hr.employee'
    
    # Campos de timesheet para técnicos
    timesheet_ids = fields.One2many(
        'inmoser.service.timesheet',
        'employee_id',
        string='Service Timesheets'
    )
    
    total_service_hours = fields.Float(
        string='Total Service Hours',
        compute='_compute_service_statistics'
    )
    
    monthly_service_hours = fields.Float(
        string='Monthly Service Hours',
        compute='_compute_service_statistics'
    )
    
    service_efficiency = fields.Float(
        string='Service Efficiency (%)',
        compute='_compute_service_statistics',
        help='Percentage of services completed on time'
    )
    
    avg_service_rating = fields.Float(
        string='Average Service Rating',
        compute='_compute_service_statistics',
        help='Average customer satisfaction rating'
    )
    
    # Inventario virtual del técnico
    virtual_inventory_ids = fields.One2many(
        'inmoser.technician.inventory',
        'technician_id',
        string='Virtual Inventory'
    )
    
    # Configuración de horarios
    service_schedule_ids = fields.One2many(
        'inmoser.technician.schedule',
        'technician_id',
        string='Service Schedule'
    )
    
    @api.depends('timesheet_ids', 'x_inmoser_service_order_ids')
    def _compute_service_statistics(self):
        """Calcular estadísticas de servicio"""
        for employee in self:
            if not employee.x_inmoser_is_technician:
                employee.total_service_hours = 0
                employee.monthly_service_hours = 0
                employee.service_efficiency = 0
                employee.avg_service_rating = 0
                continue
            
            # Horas totales de servicio
            total_hours = sum(employee.timesheet_ids.mapped('hours'))
            employee.total_service_hours = total_hours
            
            # Horas del mes actual
            current_month_start = datetime.now().replace(day=1, hour=0, minute=0, second=0)
            monthly_timesheets = employee.timesheet_ids.filtered(
                lambda t: t.date >= current_month_start.date()
            )
            employee.monthly_service_hours = sum(monthly_timesheets.mapped('hours'))
            
            # Eficiencia (servicios completados a tiempo)
            completed_orders = employee.x_inmoser_service_order_ids.filtered(
                lambda o: o.state == 'done'
            )
            
            if completed_orders:
                on_time_orders = completed_orders.filtered(
                    lambda o: o.end_date and o.scheduled_date and 
                    o.end_date <= o.scheduled_date + timedelta(hours=2)  # 2 horas de tolerancia
                )
                employee.service_efficiency = (len(on_time_orders) / len(completed_orders)) * 100
                
                # Rating promedio
                rated_orders = completed_orders.filtered(lambda o: o.customer_satisfaction)
                if rated_orders:
                    total_rating = sum(int(o.customer_satisfaction) for o in rated_orders)
                    employee.avg_service_rating = total_rating / len(rated_orders)
                else:
                    employee.avg_service_rating = 0
            else:
                employee.service_efficiency = 0
                employee.avg_service_rating = 0
    
    def action_view_service_timesheets(self):
        """Ver timesheets de servicio"""
        self.ensure_one()
        
        return {
            'type': 'ir.actions.act_window',
            'name': _('Service Timesheets - %s') % self.name,
            'res_model': 'inmoser.service.timesheet',
            'view_mode': 'tree,form',
            'domain': [('employee_id', '=', self.id)],
            'context': {'default_employee_id': self.id},
        }
    
    def action_view_virtual_inventory(self):
        """Ver inventario virtual"""
        self.ensure_one()
        
        return {
            'type': 'ir.actions.act_window',
            'name': _('Virtual Inventory - %s') % self.name,
            'res_model': 'inmoser.technician.inventory',
            'view_mode': 'tree,form',
            'domain': [('technician_id', '=', self.id)],
            'context': {'default_technician_id': self.id},
        }

class ServiceTimesheet(models.Model):
    """
    Timesheet específico para órdenes de servicio
    """
    _name = 'inmoser.service.timesheet'
    _description = 'Service Timesheet'
    _order = 'date desc, id desc'
    
    employee_id = fields.Many2one(
        'hr.employee',
        string='Technician',
        required=True,
        domain=[('x_inmoser_is_technician', '=', True)]
    )
    
    service_order_id = fields.Many2one(
        'inmoser.service.order',
        string='Service Order',
        required=True
    )
    
    date = fields.Date(
        string='Date',
        required=True,
        default=fields.Date.today
    )
    
    start_time = fields.Datetime(
        string='Start Time',
        required=True
    )
    
    end_time = fields.Datetime(
        string='End Time'
    )
    
    hours = fields.Float(
        string='Hours',
        compute='_compute_hours',
        store=True
    )
    
    description = fields.Text(
        string='Description',
        required=True
    )
    
    activity_type = fields.Selection([
        ('travel', 'Travel Time'),
        ('diagnosis', 'Diagnosis'),
        ('repair', 'Repair Work'),
        ('testing', 'Testing'),
        ('documentation', 'Documentation'),
        ('customer_interaction', 'Customer Interaction'),
        ('other', 'Other')
    ], string='Activity Type', required=True, default='repair')
    
    @api.depends('start_time', 'end_time')
    def _compute_hours(self):
        """Calcular horas trabajadas"""
        for timesheet in self:
            if timesheet.start_time and timesheet.end_time:
                delta = timesheet.end_time - timesheet.start_time
                timesheet.hours = delta.total_seconds() / 3600
            else:
                timesheet.hours = 0
    
    @api.onchange('service_order_id')
    def _onchange_service_order_id(self):
        """Actualizar información al cambiar orden de servicio"""
        if self.service_order_id:
            self.description = f"Work on {self.service_order_id.name} - {self.service_order_id.equipment_id.name}"

class TechnicianInventory(models.Model):
    """
    Inventario virtual del técnico
    """
    _name = 'inmoser.technician.inventory'
    _description = 'Technician Virtual Inventory'
    
    technician_id = fields.Many2one(
        'hr.employee',
        string='Technician',
        required=True,
        domain=[('x_inmoser_is_technician', '=', True)]
    )
    
    product_id = fields.Many2one(
        'product.product',
        string='Product',
        required=True,
        domain=[('type', 'in', ['product', 'consu'])]
    )
    
    allocated_quantity = fields.Float(
        string='Allocated Quantity',
        help='Quantity allocated to this technician'
    )
    
    available_quantity = fields.Float(
        string='Available Quantity',
        help='Quantity currently available'
    )
    
    used_quantity = fields.Float(
        string='Used Quantity',
        compute='_compute_used_quantity',
        help='Quantity used in service orders'
    )
    
    last_replenishment = fields.Date(
        string='Last Replenishment'
    )
    
    min_quantity = fields.Float(
        string='Minimum Quantity',
        help='Minimum quantity to maintain'
    )
    
    @api.depends('allocated_quantity', 'available_quantity')
    def _compute_used_quantity(self):
        """Calcular cantidad utilizada"""
        for inventory in self:
            inventory.used_quantity = inventory.allocated_quantity - inventory.available_quantity
    
    def action_replenish_stock(self):
        """Reabastecer stock del técnico"""
        self.ensure_one()
        
        # Crear wizard de reabastecimiento
        return {
            'type': 'ir.actions.act_window',
            'name': _('Replenish Stock'),
            'res_model': 'inmoser.technician.replenish.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_technician_id': self.technician_id.id,
                'default_product_id': self.product_id.id,
                'default_current_quantity': self.available_quantity,
            }
        }

class TechnicianSchedule(models.Model):
    """
    Horario de trabajo del técnico
    """
    _name = 'inmoser.technician.schedule'
    _description = 'Technician Schedule'
    
    technician_id = fields.Many2one(
        'hr.employee',
        string='Technician',
        required=True,
        domain=[('x_inmoser_is_technician', '=', True)]
    )
    
    day_of_week = fields.Selection([
        ('0', 'Monday'),
        ('1', 'Tuesday'),
        ('2', 'Wednesday'),
        ('3', 'Thursday'),
        ('4', 'Friday'),
        ('5', 'Saturday'),
        ('6', 'Sunday')
    ], string='Day of Week', required=True)
    
    start_time = fields.Float(
        string='Start Time',
        required=True,
        help='Start time in hours (e.g., 8.5 for 8:30 AM)'
    )
    
    end_time = fields.Float(
        string='End Time',
        required=True,
        help='End time in hours (e.g., 17.5 for 5:30 PM)'
    )
    
    max_services = fields.Integer(
        string='Max Services per Day',
        default=5,
        help='Maximum number of services that can be scheduled for this day'
    )
    
    is_available = fields.Boolean(
        string='Available',
        default=True
    )
    
    @api.constrains('start_time', 'end_time')
    def _check_times(self):
        """Validar horarios"""
        for schedule in self:
            if schedule.start_time >= schedule.end_time:
                raise ValidationError(_('End time must be after start time.'))
            
            if schedule.start_time < 0 or schedule.end_time > 24:
                raise ValidationError(_('Times must be between 0 and 24 hours.'))

class ServiceOrderHRIntegration(models.Model):
    """
    Integración de órdenes de servicio con HR
    """
    _inherit = 'inmoser.service.order'
    
    timesheet_ids = fields.One2many(
        'inmoser.service.timesheet',
        'service_order_id',
        string='Timesheets'
    )
    
    total_timesheet_hours = fields.Float(
        string='Total Hours',
        compute='_compute_timesheet_hours'
    )
    
    @api.depends('timesheet_ids', 'timesheet_ids.hours')
    def _compute_timesheet_hours(self):
        """Calcular horas totales de timesheet"""
        for order in self:
            order.total_timesheet_hours = sum(order.timesheet_ids.mapped('hours'))
    
    def action_start_timesheet(self):
        """Iniciar timesheet para el servicio"""
        self.ensure_one()
        
        if not self.assigned_technician_id:
            raise UserError(_('No technician assigned to this service order.'))
        
        # Verificar si ya hay un timesheet activo
        active_timesheet = self.timesheet_ids.filtered(lambda t: not t.end_time)
        
        if active_timesheet:
            raise UserError(_('There is already an active timesheet for this service order.'))
        
        # Crear nuevo timesheet
        timesheet_vals = {
            'employee_id': self.assigned_technician_id.id,
            'service_order_id': self.id,
            'date': fields.Date.today(),
            'start_time': fields.Datetime.now(),
            'description': f'Started work on {self.name}',
            'activity_type': 'diagnosis',
        }
        
        timesheet = self.env['inmoser.service.timesheet'].create(timesheet_vals)
        
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'inmoser.service.timesheet',
            'res_id': timesheet.id,
            'view_mode': 'form',
            'target': 'current',
        }
    
    def action_stop_timesheet(self):
        """Detener timesheet activo"""
        self.ensure_one()
        
        active_timesheet = self.timesheet_ids.filtered(lambda t: not t.end_time)
        
        if not active_timesheet:
            raise UserError(_('No active timesheet found for this service order.'))
        
        active_timesheet.end_time = fields.Datetime.now()
        
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Timesheet Stopped'),
                'message': _('Timesheet stopped. Total hours: %.2f') % active_timesheet.hours,
                'type': 'success',
            }
        }
    
    def action_view_timesheets(self):
        """Ver timesheets del servicio"""
        self.ensure_one()
        
        return {
            'type': 'ir.actions.act_window',
            'name': _('Timesheets - %s') % self.name,
            'res_model': 'inmoser.service.timesheet',
            'view_mode': 'tree,form',
            'domain': [('service_order_id', '=', self.id)],
            'context': {
                'default_service_order_id': self.id,
                'default_employee_id': self.assigned_technician_id.id,
            }
        }

