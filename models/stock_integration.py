# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError

class ProductProduct(models.Model):
    _inherit = 'product.product'

    custom_stock = fields.Integer(
        string="Custom Stock",
        default=0,
        help="Custom stock for internal management"
    )
    
    stock_alert_threshold = fields.Integer(
        string="Stock Alert Threshold",
        default=10,
        help="Minimum stock level to generate alerts"
    )
    
    last_inventory_date = fields.Date(
        string="Last Inventory Date",
        readonly=True
    )
    
    @api.model
    def create(self, vals):
        product = super(ProductProduct, self).create(vals)
        if 'custom_stock' in vals:
            product._update_stock_history(vals['custom_stock'], 'CREATE')
        return product
    
    def write(self, vals):
        res = super(ProductProduct, self).write(vals)
        if 'custom_stock' in vals:
            for record in self:
                record._update_stock_history(vals['custom_stock'], 'UPDATE')
        return res
    
    def _update_stock_history(self, new_stock, operation):
        """Registra el movimiento de stock en el historial"""
        self.ensure_one()
        self.env['stock.history'].create({
            'product_id': self.id,
            'previous_stock': self.custom_stock,
            'new_stock': new_stock,
            'operation': operation,
            'user_id': self.env.user.id,
        })
        
        if new_stock <= self.stock_alert_threshold:
            self._send_stock_alert()
    
    def _send_stock_alert(self):
        """Envía una alerta de stock bajo"""
        template = self.env.ref('inmoser_service_order.stock_alert_email_template')
        if template:
            template.send_mail(self.id)
    
    @api.constrains('custom_stock')
    def _check_stock(self):
        for product in self:
            if product.custom_stock < 0:
                raise ValidationError(_("Stock cannot be negative"))
    
    def action_update_inventory(self):
        """Abre el wizard para actualizar inventario"""
        return {
            'name': _('Update Inventory'),
            'type': 'ir.actions.act_window',
            'res_model': 'stock.update.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {'default_product_id': self.id}
        }
    
    @api.model
    def _send_stock_alerts(self):
        """Envía alertas de stock para todos los productos con bajo stock"""
        products = self.search([('custom_stock', '<', fields.first(self).stock_alert_threshold)])
        for product in products:
            product._send_stock_alert()

