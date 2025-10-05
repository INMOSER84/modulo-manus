# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
import logging

_logger = logging.getLogger(__name__)

class ServiceOrderStockIntegration(models.Model):
    """
    Integración del módulo de órdenes de servicio con inventario
    """
    _inherit = 'inmoser.service.order'
    
    # Campos de integración con stock
    picking_ids = fields.One2many(
        'stock.picking',
        'x_service_order_id',
        string='Stock Pickings',
        help='Stock movements related to this service order'
    )
    
    picking_count = fields.Integer(
        string='Pickings Count',
        compute='_compute_picking_count'
    )
    
    delivery_status = fields.Selection([
        ('no', 'No Delivery'),
        ('pending', 'Pending Delivery'),
        ('partial', 'Partially Delivered'),
        ('done', 'Delivered'),
    ], string='Delivery Status', compute='_compute_delivery_status', store=True)
    
    warehouse_id = fields.Many2one(
        'stock.warehouse',
        string='Warehouse',
        default=lambda self: self.env['stock.warehouse'].search([('company_id', '=', self.env.company.id)], limit=1)
    )
    
    @api.depends('picking_ids', 'picking_ids.state')
    def _compute_picking_count(self):
        """Calcular número de pickings"""
        for order in self:
            order.picking_count = len(order.picking_ids)
    
    @api.depends('picking_ids', 'picking_ids.state', 'refaction_line_ids')
    def _compute_delivery_status(self):
        """Calcular estado de entrega"""
        for order in self:
            if not order.refaction_line_ids:
                order.delivery_status = 'no'
            elif not order.picking_ids:
                order.delivery_status = 'pending'
            else:
                done_pickings = order.picking_ids.filtered(lambda p: p.state == 'done')
                if not done_pickings:
                    order.delivery_status = 'pending'
                elif len(done_pickings) == len(order.picking_ids):
                    order.delivery_status = 'done'
                else:
                    order.delivery_status = 'partial'
    
    def action_create_delivery(self):
        """Crear entrega para las refacciones"""
        self.ensure_one()
        
        if not self.refaction_line_ids:
            raise UserError(_('No parts to deliver for this service order.'))
        
        if self.delivery_status == 'done':
            raise UserError(_('All parts have already been delivered.'))
        
        # Crear picking
        picking_vals = self._prepare_picking_vals()
        picking = self.env['stock.picking'].create(picking_vals)
        
        # Crear movimientos de stock
        self._create_stock_moves(picking)
        
        # Confirmar picking
        picking.action_confirm()
        picking.action_assign()
        
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'stock.picking',
            'res_id': picking.id,
            'view_mode': 'form',
            'target': 'current',
        }
    
    def _prepare_picking_vals(self):
        """Preparar valores para el picking"""
        return {
            'partner_id': self.partner_id.id,
            'picking_type_id': self._get_picking_type().id,
            'location_id': self.warehouse_id.lot_stock_id.id,
            'location_dest_id': self.partner_id.property_stock_customer.id,
            'origin': self.name,
            'x_service_order_id': self.id,
            'company_id': self.company_id.id,
        }
    
    def _create_stock_moves(self, picking):
        """Crear movimientos de stock"""
        for line in self.refaction_line_ids:
            if line.product_id.type in ['product', 'consu']:
                move_vals = {
                    'name': line.product_id.name,
                    'product_id': line.product_id.id,
                    'product_uom_qty': line.quantity,
                    'product_uom': line.product_id.uom_id.id,
                    'picking_id': picking.id,
                    'location_id': picking.location_id.id,
                    'location_dest_id': picking.location_dest_id.id,
                    'company_id': self.company_id.id,
                }
                
                self.env['stock.move'].create(move_vals)
    
    def _get_picking_type(self):
        """Obtener tipo de picking para entregas"""
        picking_type = self.env['stock.picking.type'].search([
            ('code', '=', 'outgoing'),
            ('warehouse_id', '=', self.warehouse_id.id)
        ], limit=1)
        
        if not picking_type:
            raise UserError(_('No outgoing picking type found for warehouse %s') % self.warehouse_id.name)
        
        return picking_type
    
    def action_view_pickings(self):
        """Ver pickings relacionados"""
        self.ensure_one()
        
        if not self.picking_ids:
            raise UserError(_('No deliveries found for this service order.'))
        
        return {
            'type': 'ir.actions.act_window',
            'name': _('Deliveries'),
            'res_model': 'stock.picking',
            'view_mode': 'tree,form',
            'domain': [('id', 'in', self.picking_ids.ids)],
            'context': {'create': False},
        }
    
    def action_check_stock_availability(self):
        """Verificar disponibilidad de stock"""
        self.ensure_one()
        
        if not self.refaction_line_ids:
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': _('No Parts Required'),
                    'message': _('This service order does not require any parts.'),
                    'type': 'info',
                }
            }
        
        availability_info = []
        all_available = True
        
        for line in self.refaction_line_ids:
            if line.product_id.type == 'product':
                available_qty = line.product_id.qty_available
                
                if available_qty >= line.quantity:
                    status = _('Available')
                    status_class = 'success'
                else:
                    status = _('Insufficient Stock')
                    status_class = 'danger'
                    all_available = False
                
                availability_info.append({
                    'product': line.product_id.name,
                    'required': line.quantity,
                    'available': available_qty,
                    'status': status,
                    'status_class': status_class
                })
        
        # Crear mensaje de disponibilidad
        message_parts = []
        for info in availability_info:
            message_parts.append(
                f"• {info['product']}: {info['required']} required, "
                f"{info['available']} available - {info['status']}"
            )
        
        message = '\n'.join(message_parts)
        
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Stock Availability'),
                'message': message,
                'type': 'success' if all_available else 'warning',
                'sticky': True,
            }
        }

class StockPickingServiceOrder(models.Model):
    """
    Extensión del modelo de pickings para vincular con órdenes de servicio
    """
    _inherit = 'stock.picking'
    
    x_service_order_id = fields.Many2one(
        'inmoser.service.order',
        string='Service Order',
        help='Service order related to this delivery'
    )
    
    def action_view_service_order(self):
        """Ver orden de servicio relacionada"""
        self.ensure_one()
        
        if not self.x_service_order_id:
            raise UserError(_('No service order found for this delivery.'))
        
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'inmoser.service.order',
            'res_id': self.x_service_order_id.id,
            'view_mode': 'form',
            'target': 'current',
        }

class ProductTemplateServiceOrder(models.Model):
    """
    Extensión del modelo de productos para servicios
    """
    _inherit = 'product.template'
    
    is_service_part = fields.Boolean(
        string='Is Service Part',
        help='This product is commonly used in service orders'
    )
    
    service_category = fields.Selection([
        ('electronic', 'Electronic Component'),
        ('mechanical', 'Mechanical Part'),
        ('consumable', 'Consumable'),
        ('tool', 'Tool'),
        ('other', 'Other')
    ], string='Service Category')
    
    min_stock_service = fields.Float(
        string='Minimum Stock for Services',
        help='Minimum stock level to maintain for service operations'
    )
    
    service_order_count = fields.Integer(
        string='Used in Service Orders',
        compute='_compute_service_order_count'
    )
    
    def _compute_service_order_count(self):
        """Calcular uso en órdenes de servicio"""
        for product in self:
            count = self.env['inmoser.service.order.refaction.line'].search_count([
                ('product_id', 'in', product.product_variant_ids.ids)
            ])
            product.service_order_count = count
    
    def action_view_service_orders(self):
        """Ver órdenes de servicio que usan este producto"""
        self.ensure_one()
        
        refaction_lines = self.env['inmoser.service.order.refaction.line'].search([
            ('product_id', 'in', self.product_variant_ids.ids)
        ])
        
        service_order_ids = refaction_lines.mapped('service_order_id').ids
        
        return {
            'type': 'ir.actions.act_window',
            'name': _('Service Orders using %s') % self.name,
            'res_model': 'inmoser.service.order',
            'view_mode': 'tree,form',
            'domain': [('id', 'in', service_order_ids)],
            'context': {'create': False},
        }

class StockQuant(models.Model):
    """
    Extensión para alertas de stock bajo en productos de servicio
    """
    _inherit = 'stock.quant'
    
    @api.model
    def _check_service_parts_stock(self):
        """Verificar stock bajo en productos de servicio"""
        service_products = self.env['product.product'].search([
            ('is_service_part', '=', True),
            ('type', '=', 'product')
        ])
        
        low_stock_products = []
        
        for product in service_products:
            if product.qty_available < product.min_stock_service:
                low_stock_products.append({
                    'product': product.name,
                    'current_stock': product.qty_available,
                    'min_stock': product.min_stock_service,
                })
        
        if low_stock_products:
            # Crear actividad para el responsable de compras
            purchase_users = self.env.ref('purchase.group_purchase_user').users
            
            if purchase_users:
                message_parts = []
                for info in low_stock_products:
                    message_parts.append(
                        f"• {info['product']}: {info['current_stock']} "
                        f"(min: {info['min_stock']})"
                    )
                
                message = _('Low stock alert for service parts:\n%s') % '\n'.join(message_parts)
                
                self.env['mail.activity'].create({
                    'activity_type_id': self.env.ref('mail.mail_activity_data_todo').id,
                    'user_id': purchase_users[0].id,
                    'res_model': 'product.product',
                    'res_id': low_stock_products[0]['product'].id if low_stock_products else False,
                    'summary': _('Low Stock Alert - Service Parts'),
                    'note': message,
                })
        
        return low_stock_products

