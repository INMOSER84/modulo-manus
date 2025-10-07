k# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
import logging
from datetime import datetime

_logger = logging.getLogger(__name__)

class HREmployeeInmoser(models.Model):
    """
    Extensión del modelo de empleados para métricas de desempeño y horas de servicio
    """
    _inherit = 'hr.employee'

    # =========================================================
    # === CAMPOS DE SERVICIO Y MÉTRICAS ===
    # =========================================================
    timesheet_ids = fields.One2many(
        'inmoser.service.timesheet', 'employee_id',
        string='Registros de tiempos de servicio'
    )

    total_service_hours = fields.Float(
        string='Horas totales',
        compute='_compute_service_statistics',
        store=True
    )

    monthly_service_hours = fields.Float(
        string='Horas del mes actual',
        compute='_compute_service_statistics',
        store=True
    )

    service_efficiency = fields.Float(
        string='Eficiencia (%)',
        compute='_compute_service_statistics',
        store=True,
        help='Porcentaje de tareas completadas dentro del tiempo estimado'
    )

    avg_service_rating = fields.Float(
        string='Calificación promedio',
        compute='_compute_service_statistics',
        store=True,
        help='Calificación promedio de satisfacción del empleado'
    )

    # =========================================================
    # === VALIDACIONES Y RESTRICCIONES ===
    # =========================================================
    x_inmoser_max_daily_hours = fields.Float(
        string='Horas máximas por día',
        default=8.0,
        help='Número máximo de horas que un empleado puede registrar por día'
    )

    @api.constrains('x_inmoser_max_daily_hours')
    def _check_max_daily_hours(self):
        for employee in self:
            if employee.x_inmoser_max_daily_hours <= 0:
                raise ValidationError(_("Las horas máximas por día deben ser mayores que cero."))

    # =========================================================
    # === CÁLCULOS DE MÉTRICAS ===
    # =========================================================
    @api.depends('timesheet_ids', 'timesheet_ids.hours', 'timesheet_ids.rating')
    def _compute_service_statistics(self):
        today = fields.Date.today()
        for employee in self:
            timesheets = employee.timesheet_ids

            # Total de horas
            total_hours = sum(timesheets.mapped('hours'))
            employee.total_service_hours = total_hours

            # Horas del mes actual
            monthly_hours = sum(t.hours for t in timesheets if t.date and t.date.month == today.month)
            employee.monthly_service_hours = monthly_hours

            # Eficiencia basada en completitud y tiempo estimado
            completed = timesheets.filtered(lambda t: t.completed)
            on_time = completed.filtered(lambda t: t.hours <= t.estimated_hours)
            employee.service_efficiency = (len(on_time) / len(completed) * 100) if completed else 0.0

            # Calificación promedio
            ratings = [t.rating for t in timesheets if t.rating is not None]
            employee.avg_service_rating = sum(ratings)/len(ratings) if ratings else 0.0

    # =========================================================
    # === ACCIONES OPERATIVAS ===
    # =========================================================
    def action_view_timesheets(self):
        """Abrir los timesheets del empleado"""
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': _('Timesheets - %s') % self.name,
            'res_model': 'inmoser.service.timesheet',
            'view_mode': 'tree,form',
            'domain': [('employee_id', '=', self.id)],
            'context': {'default_employee_id': self.id},
        }

class ServiceTimesheet(models.Model):
    """
    Timesheet local independiente para registro de actividades y horas.
    """
    _name = 'inmoser.service.timesheet'
    _description = 'Timesheet de Servicio'
    _order = 'date desc, id desc'

    employee_id = fields.Many2one(
        'hr.employee',
        string='Empleado',
        required=True
    )

    date = fields.Date(
        string='Fecha',
        required=True,
        default=fields.Date.today
    )

    description = fields.Text(
        string='Descripción',
        required=True
    )

    estimated_hours = fields.Float(
        string='Horas estimadas',
        default=1.0
    )

    hours = fields.Float(
        string='Horas registradas'
    )

    completed = fields.Boolean(
        string='Completado',
        default=False
    )

    rating = fields.Float(
        string='Calificación',
        help='Calificación de desempeño del empleado en esta tarea'
    )

    @api.constrains('hours')
    def _check_hours_positive(self):
        for record in self:
            if record.hours < 0:
                raise ValidationError(_("Las horas registradas no pueden ser negativas."))
