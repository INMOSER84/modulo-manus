from odoo import models, fields, api, _
from odoo.exceptions import ValidationError

class ServiceCompleteWizard(models.TransientModel):
    _name = 'service.complete.wizard'
    _description = 'Wizard para Completar Servicio'
    
    service_order_id = fields.Many2one('service.order', string="Orden de Servicio", required=True)
    end_date = fields.Datetime(string="Fecha de Finalización", default=fields.Datetime.now, required=True)
    duration = fields.Float(string="Duración (horas)", compute='_compute_duration', store=True)
    total_cost = fields.Float(string="Costo Total", compute='_compute_total_cost', store=True)
    notes = fields.Text(string="Notas")
    parts_used = fields.One2many('service.complete.wizard.line', 'wizard_id', string="Partes Utilizadas")
    
    @api.depends('end_date', 'service_order_id.start_date')
    def _compute_duration(self):
        for wizard in self:
            if wizard.end_date and wizard.service_order_id.start_date:
                start = fields.Datetime.from_string(wizard.service_order_id.start_date)
                end = fields.Datetime.from_string(wizard.end_date)
                wizard.duration = (end - start).total_seconds() / 3600
    
    @api.depends('parts_used.price', 'parts_used.quantity', 'service_order_id.service_type_id.price')
    def _compute_total_cost(self):
        for wizard in self:
            service_cost = wizard.service_order_id.service_type_id.price or 0
            parts_cost = sum(line.price * line.quantity for line in wizard.parts_used)
            wizard.total_cost = service_cost + parts_cost
    
    @api.model
    def default_get(self, fields):
        res = super(ServiceCompleteWizard, self).default_get(fields)
        if self.env.context.get('active_id') and self.env.context.get('active_model') == 'service.order':
            service_order = self.env['service.order'].browse(self.env.context['active_id'])
            res['service_order_id'] = service_order.id
            # Cargar partes existentes
            parts_lines = []
            for line in service_order.parts_used:
                parts_lines.append({
                    'product_id': line.product_id.id,
                    'description': line.description,
                    'quantity': line.quantity,
                    'price': line.price,
                })
            res['parts_used'] = [(0, 0, line) for line in parts_lines]
        return res
    
    def action_complete_service(self):
        self.ensure_one()
        service_order = self.service_order_id
        
        # Validar stock
        for line in self.parts_used:
            if line.product_id.custom_stock < line.quantity:
                raise ValidationError(_(
                    "Stock insuficiente para %s. Disponible: %d, Solicitado: %d"
                ) % (line.product_id.name, line.product_id.custom_stock, line.quantity))
        
        # Actualizar orden de servicio
        service_order.write({
            'end_date': self.end_date,
            'duration': self.duration,
            'total_cost': self.total_cost,
            'notes': self.notes,
            'state': 'done',
        })
        
        # Actualizar partes utilizadas
        # Eliminar líneas existentes
        service_order.parts_used.unlink()
        # Crear nuevas líneas
        for line in self.parts_used:
            self.env['service.order.refaction.line'].create({
                'order_id': service_order.id,
                'product_id': line.product_id.id,
                'description': line.description,
                'quantity': line.quantity,
                'price': line.price,
            })
            # Actualizar stock
            line.product_id.custom_stock -= line.quantity
            line.product_id.last_inventory_date = fields.Date.today()
        
        # Crear factura si es necesario
        if service_order.is_sale_order:
            service_order._create_sale_order()
        
        return {'type': 'ir.actions.act_window_close'}

class ServiceCompleteWizardLine(models.TransientModel):
    _name = 'service.complete.wizard.line'
    _description = 'Líneas del Wizard de Completar Servicio'
    
    wizard_id = fields.Many2one('service.complete.wizard', string="Wizard", required=True, ondelete='cascade')
    product_id = fields.Many2one('service.equipment', string="Producto", required=True)
    description = fields.Text(string="Descripción", required=True)
    quantity = fields.Float(string="Cantidad", required=True, default=1.0)
    price = fields.Float(string="Precio Unitario", required=True)
    
    @api.onchange('product_id')
    def _onchange_product_id(self):
        if self.product_id:
            self.description = self.product_id.name
            self.price = self.product_id.list_price
            # Verificar stock
            if self.product_id.custom_stock <= 0:
                return {
                    'warning': {
                        'title': _('Stock Agotado'),
                        'message': _('No hay stock disponible para este producto')
                    }
                }
    
    @api.onchange('quantity')
    def _onchange_quantity(self):
        if self.product_id and self.quantity > self.product_id.custom_stock:
            return {
                'warning': {
                    'title': _('Stock Insuficiente'),
                    'message': _('Solo hay %d unidades disponibles de %s') % (
                        self.product_id.custom_stock, self.product_id.name)
                }
            }
