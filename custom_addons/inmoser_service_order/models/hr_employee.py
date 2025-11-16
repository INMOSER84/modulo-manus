from odoo import fields, models
class HrEmployee(models.Model):
    _inherit = 'hr.employee'
    """
    Extensión del modelo `hr.employee` para añadir funcionalidades específicas
    de Inmoser para la gestión de técnicos de servicio.
    Incluye campos para identificar si es técnico, almacén virtual,
    horas disponibles, nivel y especialidades.
    """
    x_inmoser_is_technician = fields.Boolean(string='Es Técnico', default=False, help='Marca si el empleado es un técnico asignable a órdenes de servicio.', index=True)
    x_inmoser_virtual_warehouse_id = fields.Many2one('stock.warehouse', string='Almacén Virtual de Técnico', help='Almacén para el inventario de refacciones del técnico.', check_company=True)
    x_inmoser_available_hours = fields.Float(string='Horas Disponibles', digits=(5, 2), help='Horas disponibles del técnico para asignación de servicios.')
    x_inmoser_technician_level = fields.Selection([('junior','Junior'),('mid','Mid-Level'),('senior','Senior')], string='Nivel del Técnico')
    x_inmoser_specialty_ids = fields.Many2many('inmoser.service.specialty', string='Especialidades')
