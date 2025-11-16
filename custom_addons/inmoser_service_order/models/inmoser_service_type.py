from odoo import models, fields, api

class InmoserServiceType(models.Model):
    _name = 'inmoser.service.type'
    _description = 'Inmoser Service Type'
    _order = 'sequence, name'

    name = fields.Char(
        string='Name',
        required=True,
        translate=True
    )
    code = fields.Char(
        string='Code',
        required=True,
        help='Unique code for the service type'
    )
    description = fields.Text(
        string='Description',
        translate=True
    )
    sequence = fields.Integer(
        string='Sequence',
        default=10,
        help='Used to order service types'
    )
    active = fields.Boolean(
        string='Active',
        default=True
    )

    _sql_constraints = [
        ('code_unique', 'UNIQUE(code)', 'The service type code must be unique!')
    ]
