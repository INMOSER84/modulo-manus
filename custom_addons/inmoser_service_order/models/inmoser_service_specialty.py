from odoo import fields, models

class InmoserServiceSpecialty(models.Model):
    _name = 'inmoser.service.specialty'
    _description = 'Especialidad de Técnico de Servicio'
    """
    Modelo para definir las especialidades de los técnicos de servicio.
    Permite categorizar las habilidades de los técnicos para una asignación
    más eficiente de las órdenes de servicio.
    """
    name = fields.Char(string='Nombre de la Especialidad', required=True)
    description = fields.Text(string='Descripción')
