from odoo import models, fields, api

class StockHistory(models.Model):
    _name = 'stock.history'
    _description = 'Historial de Movimientos de Stock'
    _order = 'date desc'
    
    product_id = fields.Many2one('service.equipment', string="Producto", required=True)
    previous_stock = fields.Integer(string="Stock Anterior")
    new_stock = fields.Integer(string="Stock Nuevo")
    difference = fields.Integer(string="Diferencia", compute='_compute_difference')
    operation = fields.Selection([
        ('CREATE', 'Creación'),
        ('UPDATE', 'Actualización'),
        ('SALE', 'Venta'),
        ('SERVICE', 'Servicio'),
        ('CANCEL', 'Cancelación'),
        ('ADJUST', 'Ajuste')
    ], string="Operación")
    date = fields.Datetime(string="Fecha", default=fields.Datetime.now)
    user_id = fields.Many2one('res.users', string="Usuario")
    
    @api.depends('previous_stock', 'new_stock')
    def _compute_difference(self):
        for record in self:
            record.difference = record.new_stock - record.previous_stock
