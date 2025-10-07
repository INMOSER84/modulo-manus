# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError

class ServiceOrderRefactionLine(models.Model):
    _name = 'inmoser.service.order.refaction.line'
    _description = 'Service Order Refaction Line'
    _order = 'order_id, sequence, id'

    order_id = fields.Many2one(
        'inmoser.service.order',
        string='Service Order',
        required=True,
        ondelete='cascade'
    )
    
    sequence = fields.Integer(
        string='Sequence',
        default=10
    )
    
    product_id = fields.Many2one(
        'product.product',
        string='Product',
        required=True
    )
    
    description = fields.Text(
        string='Description'
    )
    
    quantity = fields.Float(
        string='Quantity',
        required=True,
        default=1.0
    )
    
    unit_price = fields.Float(
        string='Unit Price',
        required=True
    )
    
    total_price = fields.Float(
        string='Total Price',
        compute='_compute_total_price',
        store=True
    )
    
    reserved_stock = fields.Float(
        string='Reserved Stock',
        readonly=True
    )
    
    @api.depends('quantity', 'unit_price')
    def _compute_total_price(self):
        for line in self:
            line.total_price = line.quantity * line.unit_price
    
    @api.onchange('product_id')
    def _onchange_product_id(self):
        if self.product_id:
            self.description = self.product_id.name
            self.unit_price = self.product_id.list_price
        else:
            self.description = ''
            self.unit_price = 0.0
    
    def reserve_stock(self):
        """Reserva stock para esta línea"""
        if self.product_id.custom_stock < self.quantity:
            raise ValidationError(_(
                "Not enough stock for %s. Available: %s, Required: %s"
            ) % (self.product_id.name, self.product_id.custom_stock, self.quantity))
        
        self.product_id.custom_stock -= self.quantity
        self.reserved_stock = self.quantity
        
        # Registrar en historial
        self.env['stock.history'].create({
            'product_id': self.product_id.id,
            'previous_stock': self.product_id.custom_stock + self.quantity,
            'new_stock': self.product_id.custom_stock,
            'operation': 'RESERVE',
            'user_id': self.env.user.id,
        })
    
    def consume_stock(self):
        """Consume el stock reservado"""
        if self.reserved_stock > 0:
            # Ya está reservado, no hacer nada adicional
            pass
        else:
            # Si no está reservado, consumir directamente
            if self.product_id.custom_stock < self.quantity:
                raise ValidationError(_(
                    "Not enough stock for %s. Available: %s, Required: %s"
                ) % (self.product_id.name, self.product_id.custom_stock, self.quantity))
            
            self.product_id.custom_stock -= self.quantity
            
            # Registrar en historial
            self.env['stock.history'].create({
                'product_id': self.product_id.id,
                'previous_stock': self.product_id.custom_stock + self.quantity,
                'new_stock': self.product_id.custom_stock,
                'operation': 'CONSUME',
                'user_id': self.env.user.id,
            })
    
    def cancel_reservation(self):
        """Cancela la reserva de stock"""
        if self.reserved_stock > 0:
            self.product_id.custom_stock += self.reserved_stock
            
            # Registrar en historial
            self.env['stock.history'].create({
                'product_id': self.product_id.id,
                'previous_stock': self.product_id.custom_stock - self.reserved_stock,
                'new_stock': self.product_id.custom_stock,
                'operation': 'CANCEL_RESERVE',
                'user_id': self.env.user.id,
            })
            
            self.reserved_stock = 0
