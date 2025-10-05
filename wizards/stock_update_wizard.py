from odoo import models, fields, api

class StockUpdateWizard(models.TransientModel):
    _name = 'stock.update.wizard'
    _description = 'Wizard para Actualizar Inventario'
    
    product_id = fields.Many2one('service.equipment', string="Producto")
    new_stock = fields.Integer(string="Nuevo Stock", required=True)
    notes = fields.Text(string="Notas")
    
    @api.model
    def default_get(self, fields):
        res = super(StockUpdateWizard, self).default_get(fields)
        if self.env.context.get('default_product_id'):
            product = self.env['service.equipment'].browse(self.env.context['default_product_id'])
            res['product_id'] = product.id
            res['new_stock'] = product.custom_stock
        return res
    
    def action_update_stock(self):
        self.product_id.custom_stock = self.new_stock
        self.product_id.last_inventory_date = fields.Date.today()
        return {'type': 'ir.actions.act_window_close'}
