# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class ServiceOrderRefactionLine(models.Model):
    _name = 'inmoser.service.order.refaction.line'
    _description = 'Service Order Refaction Line'
    _order = 'order_id, sequence, id'
    _rec_name = 'product_id'

    # Relación principal
    order_id = fields.Many2one(
        'inmoser.service.order',
        string='Service Order',
        required=True,
        ondelete='cascade',
        index=True
    )
    
    # Información del producto
    product_id = fields.Many2one(
        'product.product',
        string='Product/Refaction',
        required=True,
        domain=[('type', 'in', ['product', 'consu'])]
    )
    
    product_uom_id = fields.Many2one(
        'uom.uom',
        string='Unit of Measure',
        related='product_id.uom_id',
        readonly=True
    )
    
    # Cantidades y precios
    quantity = fields.Float(
        string='Quantity',
        required=True,
        default=1.0,
        digits='Product Unit of Measure'
    )
    
    unit_price = fields.Float(
        string='Unit Price',
        required=True,
        digits='Product Price'
    )
    
    total_price = fields.Float(
        string='Total Price',
        compute='_compute_total_price',
        store=True,
        digits='Product Price'
    )
    
    # Información adicional
    description = fields.Text(
        string='Description',
        help='Descripción adicional de la refacción o trabajo'
    )
    
    sequence = fields.Integer(
        string='Sequence',
        default=10,
        help='Orden de visualización en la lista'
    )
    
    # Estado y control
    state = fields.Selection(
        related='order_id.state',
        string='Order State',
        readonly=True,
        store=True
    )
    
    # Información de inventario
    stock_move_id = fields.Many2one(
        'stock.move',
        string='Stock Move',
        help='Movimiento de inventario asociado',
        readonly=True
    )
    
    available_qty = fields.Float(
        string='Available Quantity',
        compute='_compute_available_qty',
        help='Cantidad disponible en el almacén del técnico'
    )
    
    # Campos relacionados para facilitar búsquedas
    partner_id = fields.Many2one(
        related='order_id.partner_id',
        string='Customer',
        readonly=True,
        store=True
    )
    
    technician_id = fields.Many2one(
        related='order_id.assigned_technician_id',
        string='Technician',
        readonly=True,
        store=True
    )

    @api.depends('quantity', 'unit_price')
    def _compute_total_price(self):
        """Calcula el precio total de la línea"""
        for line in self:
            line.total_price = line.quantity * line.unit_price

    @api.depends('product_id', 'technician_id')
    def _compute_available_qty(self):
        """Calcula la cantidad disponible en el almacén del técnico"""
        for line in self:
            if line.product_id and line.technician_id and line.technician_id.x_inmoser_virtual_warehouse_id:
                # Buscar cantidad disponible en el almacén virtual del técnico
                stock_quant = self.env['stock.quant'].search([
                    ('product_id', '=', line.product_id.id),
                    ('location_id', '=', line.technician_id.x_inmoser_virtual_warehouse_id.id)
                ], limit=1)
                line.available_qty = stock_quant.quantity if stock_quant else 0.0
            else:
                line.available_qty = 0.0

    @api.onchange('product_id')
    def _onchange_product_id(self):
        """Actualiza precio unitario al cambiar producto"""
        if self.product_id:
            self.unit_price = self.product_id.list_price
            if not self.description:
                self.description = self.product_id.name

    @api.onchange('quantity', 'unit_price')
    def _onchange_quantity_price(self):
        """Actualiza total al cambiar cantidad o precio"""
        self.total_price = self.quantity * self.unit_price

    @api.constrains('quantity')
    def _check_quantity(self):
        """Valida que la cantidad sea positiva"""
        for line in self:
            if line.quantity <= 0:
                raise ValidationError(_('La cantidad debe ser mayor que cero.'))

    @api.constrains('unit_price')
    def _check_unit_price(self):
        """Valida que el precio unitario no sea negativo"""
        for line in self:
            if line.unit_price < 0:
                raise ValidationError(_('El precio unitario no puede ser negativo.'))

    def check_availability(self):
        """
        Verifica si hay suficiente stock disponible para esta línea
        
        Returns:
            bool: True si hay suficiente stock, False si no
        """
        self.ensure_one()
        return self.available_qty >= self.quantity

    def reserve_stock(self):
        """
        Reserva el stock necesario para esta línea de refacción
        
        Returns:
            bool: True si se pudo reservar, False si no
        """
        self.ensure_one()
        
        if not self.check_availability():
            return False
        
        if not self.technician_id.x_inmoser_virtual_warehouse_id:
            return False
        
        # Crear movimiento de stock para reservar
        stock_move_vals = {
            'name': f"Reserva para OS {self.order_id.name}",
            'product_id': self.product_id.id,
            'product_uom_qty': self.quantity,
            'product_uom': self.product_uom_id.id,
            'location_id': self.technician_id.x_inmoser_virtual_warehouse_id.id,
            'location_dest_id': self.env.ref('stock.stock_location_customers').id,
            'origin': self.order_id.name,
            'state': 'draft',
        }
        
        stock_move = self.env['stock.move'].create(stock_move_vals)
        self.stock_move_id = stock_move.id
        
        return True

    def consume_stock(self):
        """
        Consume el stock reservado al finalizar el servicio
        
        Returns:
            bool: True si se pudo consumir, False si no
        """
        self.ensure_one()
        
        if self.stock_move_id and self.stock_move_id.state == 'draft':
            self.stock_move_id._action_confirm()
            self.stock_move_id._action_done()
            return True
        
        return False

    def cancel_reservation(self):
        """Cancela la reserva de stock"""
        self.ensure_one()
        
        if self.stock_move_id and self.stock_move_id.state in ['draft', 'waiting', 'confirmed']:
            self.stock_move_id._action_cancel()
            return True
        
        return False

    @api.model
    def get_most_used_products(self, service_type_id=None, limit=10):
        """
        Obtiene los productos más utilizados en órdenes de servicio
        
        Args:
            service_type_id (int, optional): ID del tipo de servicio para filtrar
            limit (int): Número máximo de productos a retornar
            
        Returns:
            list: Lista de diccionarios con producto y cantidad total utilizada
        """
        domain = []
        if service_type_id:
            domain.append(('order_id.service_type_id', '=', service_type_id))
        
        # Agrupar por producto y sumar cantidades
        self.env.cr.execute("""
            SELECT 
                product_id,
                SUM(quantity) as total_qty,
                COUNT(*) as usage_count
            FROM inmoser_service_order_refaction_line
            WHERE %s
            GROUP BY product_id
            ORDER BY usage_count DESC, total_qty DESC
            LIMIT %s
        """, (domain and f"order_id IN (SELECT id FROM inmoser_service_order WHERE {' AND '.join([f'{d[0]} {d[1]} {d[2]}' for d in domain])})" or "1=1", limit))
        
        results = []
        for row in self.env.cr.fetchall():
            product = self.env['product.product'].browse(row[0])
            results.append({
                'product': product,
                'total_quantity': row[1],
                'usage_count': row[2]
            })
        
        return results

    def name_get(self):
        """Personaliza la visualización del nombre de la línea"""
        result = []
        for line in self:
            name = ''
            if line.product_id:
                name = f"{line.product_id.name}"
                if line.quantity != 1:
                    name += f" x{line.quantity}"
            else:
                name = _('New Refaction Line')
            result.append((line.id, name))
        return result

    @api.model
    def create(self, vals):
        """Override create para validaciones adicionales"""
        line = super(ServiceOrderRefactionLine, self).create(vals)
        
        # Si la orden está en estado que requiere reserva, intentar reservar
        if line.order_id.state in ['accepted'] and line.technician_id:
            line.reserve_stock()
        
        return line

    def unlink(self):
        """Override unlink para cancelar reservas antes de eliminar"""
        for line in self:
            if line.stock_move_id:
                line.cancel_reservation()
        
        return super(ServiceOrderRefactionLine, self).unlink()

