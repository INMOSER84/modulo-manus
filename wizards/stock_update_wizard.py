from odoo import models, fields, api, _
from odoo.exceptions import ValidationError

class StockUpdateWizard(models.TransientModel):
    _name = 'stock.update.wizard'
    _description = 'Wizard para Actualizar Inventario'
    
    product_id = fields.Many2one('service.equipment', string="Producto", required=True)
    new_stock = fields.Integer(string="Nuevo Stock", required=True)
    previous_stock = fields.Integer(string="Stock Anterior", readonly=True)
    notes = fields.Text(string="Notas")
    operation_type = fields.Selection([
        ('adjust', 'Ajuste'),
        ('entry', 'Entrada'),
        ('exit', 'Salida'),
        ('count', 'Conteo')
    ], string="Tipo de Operación", default='adjust', required=True)
    
    @api.model
    def default_get(self, fields):
        res = super(StockUpdateWizard, self).default_get(fields)
        if self.env.context.get('default_product_id'):
            product = self.env['service.equipment'].browse(self.env.context['default_product_id'])
            res['product_id'] = product.id
            res['previous_stock'] = product.custom_stock
            res['new_stock'] = product.custom_stock
        return res
    
    @api.onchange('product_id')
    def _onchange_product_id(self):
        if self.product_id:
            self.previous_stock = self.product_id.custom_stock
            self.new_stock = self.product_id.custom_stock
    
    @api.constrains('new_stock')
    def _check_stock(self):
        for wizard in self:
            if wizard.new_stock < 0:
                raise ValidationError(_("El stock no puede ser negativo"))
    
    def action_update_stock(self):
        self.ensure_one()
        product = self.product_id
        
        # Registrar movimiento de stock
        operation_map = {
            'adjust': 'ADJUST',
            'entry': 'ENTRY',
            'exit': 'EXIT',
            'count': 'COUNT'
        }
        
        # Actualizar stock
        product.custom_stock = self.new_stock
        product.last_inventory_date = fields.Date.today()
        
        # Crear historial
        self.env['stock.history'].create({
            'product_id': product.id,
            'previous_stock': self.previous_stock,
            'new_stock': self.new_stock,
            'operation': operation_map[self.operation_type],
            'user_id': self.env.user.id,
        })
        
        # Enviar alerta si es necesario
        if self.new_stock <= product.stock_alert_threshold:
            product._send_stock_alert()
        
        return {'type': 'ir.actions.act_window_close'}
