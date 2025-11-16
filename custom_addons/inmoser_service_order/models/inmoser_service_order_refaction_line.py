from odoo import models, fields, api

class InmoserServiceOrderRefactionLine(models.Model):
    _name = 'inmoser.service.order.refaction.line'
    _description = 'Inmoser Service Order Refaction Line'

    order_id = fields.Many2one(
        'inmoser.service.order', 
        string='Service Order', 
        required=True, 
        ondelete='cascade'
    )
    product_id = fields.Many2one(
        'product.product', 
        string='Product', 
        required=True
    )
    name = fields.Text(
        string='Description', 
        required=True
    )
    quantity = fields.Float(
        string='Quantity', 
        required=True, 
        default=1.0
    )
    price_unit = fields.Float(
        string='Unit Price', 
        required=True
    )
    price_subtotal = fields.Monetary(
        string='Subtotal', 
        compute='_compute_price_subtotal', 
        store=True
    )
    currency_id = fields.Many2one(
        related='order_id.currency_id', 
        store=True
    )

    @api.depends('quantity', 'price_unit')
    def _compute_price_subtotal(self):
        for line in self:
            line.price_subtotal = line.quantity * line.price_unit
