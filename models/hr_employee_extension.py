# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
import re


class HrEmployeeExtension(models.Model):
    _inherit = 'hr.employee'

    # Campos específicos para técnicos
    x_inmoser_is_technician = fields.Boolean(
        string='Is Technician',
        help='Indica si este empleado es un técnico de servicio',
        default=False
    )
    
    x_inmoser_virtual_warehouse_id = fields.Many2one(
        'stock.location',
        string='Virtual Warehouse',
        help='Ubicación de inventario para el almacén virtual del técnico',
        domain=[('usage', '=', 'internal')]
    )
    
    x_inmoser_available_hours = fields.Char(
        string='Available Hours',
        help='Horas disponibles del técnico (ej: 10-12,12-14,15-17)',
        default='10-12,12-14,15-17'
    )
    
    x_inmoser_technician_level = fields.Selection([
        ('junior', 'Junior'),
        ('senior', 'Senior'),
        ('expert', 'Expert'),
        ('specialist', 'Specialist')
    ], string='Technician Level', help='Nivel de experiencia del técnico')
    
    x_inmoser_specialties = fields.Text(
        string='Specialties',
        help='Especialidades y certificaciones del técnico'
    )
    
    x_inmoser_max_daily_orders = fields.Integer(
        string='Max Daily Orders',
        help='Número máximo de órdenes de servicio por día',
        default=4
    )
    
    # Relaciones
    x_inmoser_assigned_orders = fields.One2many(
        'inmoser.service.order',
        'assigned_technician_id',
        string='Assigned Service Orders',
        help='Órdenes de servicio asignadas a este técnico'
    )
    
    # Campos computados
    x_inmoser_active_orders_count = fields.Integer(
        string='Active Orders Count',
        compute='_compute_active_orders_count',
        help='Número de órdenes activas asignadas'
    )
    
    x_inmoser_completed_orders_count = fields.Integer(
        string='Completed Orders Count',
        compute='_compute_completed_orders_count',
        help='Número de órdenes completadas'
    )

    @api.depends('x_inmoser_assigned_orders.state')
    def _compute_active_orders_count(self):
        """Calcula el número de órdenes activas del técnico"""
        for employee in self:
            if employee.x_inmoser_is_technician:
                active_states = ['assigned', 'in_progress', 'pending_approval', 'accepted']
                employee.x_inmoser_active_orders_count = len(
                    employee.x_inmoser_assigned_orders.filtered(
                        lambda o: o.state in active_states
                    )
                )
            else:
                employee.x_inmoser_active_orders_count = 0

    @api.depends('x_inmoser_assigned_orders.state')
    def _compute_completed_orders_count(self):
        """Calcula el número de órdenes completadas del técnico"""
        for employee in self:
            if employee.x_inmoser_is_technician:
                employee.x_inmoser_completed_orders_count = len(
                    employee.x_inmoser_assigned_orders.filtered(
                        lambda o: o.state == 'done'
                    )
                )
            else:
                employee.x_inmoser_completed_orders_count = 0

    @api.constrains('x_inmoser_available_hours')
    def _check_available_hours_format(self):
        """Valida el formato de las horas disponibles"""
        for employee in self:
            if employee.x_inmoser_available_hours and employee.x_inmoser_is_technician:
                # Formato esperado: HH-HH,HH-HH (ej: 10-12,12-14,15-17)
                hours_pattern = r'^(\d{1,2}-\d{1,2})(,\d{1,2}-\d{1,2})*$'
                if not re.match(hours_pattern, employee.x_inmoser_available_hours):
                    raise ValidationError(_(
                        'El formato de horas disponibles no es válido. '
                        'Use el formato: HH-HH,HH-HH (ej: 10-12,12-14,15-17)'
                    ))
                
                # Validar que las horas sean válidas (0-23)
                hours_ranges = employee.x_inmoser_available_hours.split(',')
                for hour_range in hours_ranges:
                    start_hour, end_hour = hour_range.split('-')
                    if not (0 <= int(start_hour) <= 23 and 0 <= int(end_hour) <= 23):
                        raise ValidationError(_(
                            'Las horas deben estar entre 0 y 23.'
                        ))
                    if int(start_hour) >= int(end_hour):
                        raise ValidationError(_(
                            'La hora de inicio debe ser menor que la hora de fin.'
                        ))

    @api.constrains('x_inmoser_max_daily_orders')
    def _check_max_daily_orders(self):
        """Valida el número máximo de órdenes diarias"""
        for employee in self:
            if employee.x_inmoser_is_technician and employee.x_inmoser_max_daily_orders <= 0:
                raise ValidationError(_(
                    'El número máximo de órdenes diarias debe ser mayor que cero.'
                ))

    @api.onchange('x_inmoser_is_technician')
    def _onchange_is_technician(self):
        """Limpia campos específicos de técnico si se desmarca"""
        if not self.x_inmoser_is_technician:
            self.x_inmoser_virtual_warehouse_id = False
            self.x_inmoser_available_hours = False
            self.x_inmoser_technician_level = False
            self.x_inmoser_specialties = False
            self.x_inmoser_max_daily_orders = 0

    def action_view_assigned_orders(self):
        """Acción para ver las órdenes asignadas al técnico"""
        self.ensure_one()
        action = self.env.ref('inmoser_service_order.action_service_order').read()[0]
        action['domain'] = [('assigned_technician_id', '=', self.id)]
        action['context'] = {
            'default_assigned_technician_id': self.id,
            'search_default_assigned_technician_id': self.id,
        }
        return action

    def action_view_technician_calendar(self):
        """Acción para ver el calendario del técnico"""
        self.ensure_one()
        action = self.env.ref('inmoser_service_order.action_service_order_calendar').read()[0]
        action['domain'] = [('assigned_technician_id', '=', self.id)]
        action['context'] = {
            'default_assigned_technician_id': self.id,
        }
        return action

    def get_available_time_slots(self, date):
        """
        Obtiene los slots de tiempo disponibles para un técnico en una fecha específica
        
        Args:
            date (datetime.date): Fecha para la cual obtener los slots
            
        Returns:
            list: Lista de tuplas (hora_inicio, hora_fin) disponibles
        """
        self.ensure_one()
        if not self.x_inmoser_is_technician or not self.x_inmoser_available_hours:
            return []
        
        # Obtener órdenes ya programadas para esa fecha
        existing_orders = self.x_inmoser_assigned_orders.filtered(
            lambda o: o.scheduled_date and o.scheduled_date.date() == date and o.state not in ['cancelled', 'done']
        )
        
        # Convertir horas disponibles a lista de slots
        available_slots = []
        hours_ranges = self.x_inmoser_available_hours.split(',')
        
        for hour_range in hours_ranges:
            start_hour, end_hour = map(int, hour_range.split('-'))
            available_slots.append((start_hour, end_hour))
        
        # Filtrar slots ocupados (simplificado - asume 2 horas por servicio)
        occupied_hours = []
        for order in existing_orders:
            order_hour = order.scheduled_date.hour
            occupied_hours.extend([order_hour, order_hour + 1])
        
        # Filtrar slots disponibles
        free_slots = []
        for start_hour, end_hour in available_slots:
            for hour in range(start_hour, end_hour, 2):  # Slots de 2 horas
                if hour not in occupied_hours and hour + 1 not in occupied_hours:
                    free_slots.append((hour, hour + 2))
        
        return free_slots

    def check_daily_capacity(self, date):
        """
        Verifica si el técnico tiene capacidad para más órdenes en una fecha
        
        Args:
            date (datetime.date): Fecha a verificar
            
        Returns:
            bool: True si tiene capacidad, False si no
        """
        self.ensure_one()
        if not self.x_inmoser_is_technician:
            return False
        
        # Contar órdenes programadas para esa fecha
        orders_count = len(self.x_inmoser_assigned_orders.filtered(
            lambda o: o.scheduled_date and o.scheduled_date.date() == date and o.state not in ['cancelled', 'done']
        ))
        
        return orders_count < self.x_inmoser_max_daily_orders

    @api.model
    def get_available_technicians(self, date, service_type=None):
        """
        Obtiene técnicos disponibles para una fecha específica
        
        Args:
            date (datetime.date): Fecha para la cual buscar técnicos
            service_type (str, optional): Tipo de servicio para filtrar por especialidad
            
        Returns:
            recordset: Técnicos disponibles
        """
        technicians = self.search([('x_inmoser_is_technician', '=', True)])
        available_technicians = self.env['hr.employee']
        
        for technician in technicians:
            if technician.check_daily_capacity(date) and technician.get_available_time_slots(date):
                available_technicians |= technician
        
        return available_technicians

    def name_get(self):
        """Personaliza la visualización del nombre para técnicos"""
        result = []
        for employee in self:
            name = employee.name or ''
            if employee.x_inmoser_is_technician:
                level = dict(employee._fields['x_inmoser_technician_level'].selection).get(
                    employee.x_inmoser_technician_level, ''
                )
                if level:
                    name = f"{name} ({level})"
            result.append((employee.id, name))
        return result

