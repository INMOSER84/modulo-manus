# -*- coding: utf-8 -*-

from odoo import models, fields, api

class StockHistory(models.Model):
    _name = 'stock.history'
    _description = 'Stock History'
    _order = 'date desc, id'

    product_id = fields.Many2one(
        'product.product',
        string='Product',
        required=True
    )
    
    previous_stock = fields.Float(
        string='Previous Stock',
        required=True
    )
    
    new_stock = fields.Float(
        string='New Stock',
        required=True
    )
    
    operation = fields.Selection([
        ('CREATE', 'Create'),
        ('UPDATE', 'Update'),
        ('RESERVE', 'Reserve'),
        ('CONSUME', 'Consume'),
        ('CANCEL_RESERVE', 'Cancel Reserve'),
        ('RESTORE', 'Restore'),
    ], string='Operation', required=True)
    
    user_id = fields.Many2one(
        'res.users',
        string='User',
        required=True,
        default=lambda self: self.env.user
    )
    
    date = fields.Datetime(
        string='Date',
        required=True,
        default=fields.Datetime.now
    )
    
    notes = fields.Text(
        string='Notes'
    )
