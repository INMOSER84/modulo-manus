# -*- coding: utf-8 -*-

from odoo import models, fields, api, _

class ServiceType(models.Model):
    _name = 'inmoser.service.type'
    _description = 'Service Type'
    _order = 'name'

    name = fields.Char(
        string='Service Type',
        required=True
    )
    
    description = fields.Text(
        string='Description'
    )
    
    base_price = fields.Float(
        string='Base Price',
        required=True,
        default=0.0
    )
    
    estimated_duration = fields.Float(
        string='Estimated Duration (hours)',
        help='Estimated time to complete this service type',
        default=2.0
    )
    
    active = fields.Boolean(
        string='Active',
        default=True
    )
    
    product_id = fields.Many2one(
        'product.product',
        string='Related Product',
        help='Product associated with this service type'
    )
    
    default_product_ids = fields.Many2many(
        'product.product',
        string='Default Products',
        help='Products to include by default in service orders'
    )
    
    @api.model
    def create(self, vals):
        service_type = super(ServiceType, self).create(vals)
        
        # Crear producto asociado si no existe
        if not vals.get('product_id') and vals.get('name'):
            product = self.env['product.product'].create({
                'name': vals.get('name'),
                'type': 'service',
                'list_price': vals.get('base_price', 0.0),
                'default_code': f"SRV-{service_type.id}",
            })
            service_type.product_id = product.id
        
        return service_type
    
    def write(self, vals):
        result = super(ServiceType, self).write(vals)
        
        # Actualizar producto asociado si cambia el nombre o precio
        if 'name' in vals or 'base_price' in vals:
            for record in self:
                if record.product_id:
                    update_vals = {}
                    if 'name' in vals:
                        update_vals['name'] = vals['name']
                    if 'base_price' in vals:
                        update_vals['list_price'] = vals['base_price']
                    
                    if update_vals:
                        record.product_id.write(update_vals)
        
        return result
