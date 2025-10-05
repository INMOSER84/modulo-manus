# -*- coding: utf-8 -*-

from odoo import http, fields, _
from odoo.http import request
from odoo.addons.portal.controllers.portal import CustomerPortal
from odoo.exceptions import AccessError, MissingError
import json
import logging

_logger = logging.getLogger(__name__)

class InmoserPortal(http.Controller):
    """
    Controlador del portal web de Inmoser para acceso público
    """
    
    @http.route(['/inmoser/equipment/<int:equipment_id>'], type='http', auth="public", website=True)
    def equipment_portal(self, equipment_id, **kw):
        """Portal público para ver información del equipo"""
        try:
            # Buscar equipo
            equipment = request.env['inmoser.service.equipment'].sudo().browse(equipment_id)
            
            if not equipment.exists():
                return request.render('inmoser_service_order.equipment_not_found')
            
            # Obtener órdenes de servicio del equipo
            service_orders = request.env['inmoser.service.order'].sudo().search([
                ('equipment_id', '=', equipment_id)
            ], order='create_date desc', limit=10)
            
            # Obtener orden actual (si existe)
            current_order = service_orders.filtered(lambda o: o.state not in ['done', 'cancelled'])[:1]
            
            values = {
                'equipment': equipment,
                'service_orders': service_orders,
                'current_order': current_order,
                'page_name': 'equipment_portal',
            }
            
            return request.render('inmoser_service_order.equipment_portal_template', values)
            
        except Exception as e:
            _logger.error(f"Error in equipment portal: {str(e)}")
            return request.render('inmoser_service_order.portal_error', {'error': str(e)})
    
    @http.route(['/inmoser/service-order/<int:order_id>'], type='http', auth="public", website=True)
    def service_order_portal(self, order_id, **kw):
        """Portal público para ver información de la orden de servicio"""
        try:
            # Buscar orden de servicio
            order = request.env['inmoser.service.order'].sudo().browse(order_id)
            
            if not order.exists():
                return request.render('inmoser_service_order.order_not_found')
            
            values = {
                'order': order,
                'page_name': 'service_order_portal',
            }
            
            return request.render('inmoser_service_order.service_order_portal_template', values)
            
        except Exception as e:
            _logger.error(f"Error in service order portal: {str(e)}")
            return request.render('inmoser_service_order.portal_error', {'error': str(e)})
    
    @http.route(['/inmoser/request-service'], type='http', auth="public", website=True, methods=['GET', 'POST'])
    def request_service(self, **kw):
        """Formulario para solicitar nuevo servicio"""
        if request.httprequest.method == 'POST':
            return self._process_service_request(**kw)
        
        # Obtener tipos de servicio disponibles
        service_types = request.env['inmoser.service.type'].sudo().search([
            ('active', '=', True)
        ])
        
        values = {
            'service_types': service_types,
            'page_name': 'request_service',
        }
        
        return request.render('inmoser_service_order.request_service_template', values)
    
    def _process_service_request(self, **kw):
        """Procesar solicitud de servicio"""
        try:
            # Validar datos requeridos
            required_fields = ['customer_name', 'customer_phone', 'customer_email', 
                             'equipment_type', 'service_type_id', 'reported_fault']
            
            for field in required_fields:
                if not kw.get(field):
                    raise ValueError(f"Field {field} is required")
            
            # Buscar o crear cliente
            partner = self._find_or_create_customer(kw)
            
            # Buscar o crear equipo
            equipment = self._find_or_create_equipment(partner, kw)
            
            # Crear orden de servicio
            order_vals = {
                'partner_id': partner.id,
                'equipment_id': equipment.id,
                'service_type_id': int(kw.get('service_type_id')),
                'reported_fault': kw.get('reported_fault'),
                'priority': kw.get('priority', 'normal'),
            }
            
            order = request.env['inmoser.service.order'].sudo().create(order_vals)
            
            # Redirigir al portal de la orden creada
            return request.redirect(f'/inmoser/service-order/{order.id}?success=1')
            
        except Exception as e:
            _logger.error(f"Error processing service request: {str(e)}")
            return request.render('inmoser_service_order.request_service_template', {
                'error': str(e),
                'form_data': kw,
                'service_types': request.env['inmoser.service.type'].sudo().search([('active', '=', True)])
            })
    
    def _find_or_create_customer(self, data):
        """Buscar o crear cliente"""
        # Buscar por email o teléfono
        partner = request.env['res.partner'].sudo().search([
            '|', 
            ('email', '=', data.get('customer_email')),
            ('phone', '=', data.get('customer_phone'))
        ], limit=1)
        
        if not partner:
            # Crear nuevo cliente
            partner_vals = {
                'name': data.get('customer_name'),
                'phone': data.get('customer_phone'),
                'mobile': data.get('customer_mobile'),
                'email': data.get('customer_email'),
                'street': data.get('customer_address'),
                'x_inmoser_is_service_client': True,
            }
            partner = request.env['res.partner'].sudo().create(partner_vals)
        
        return partner
    
    def _find_or_create_equipment(self, partner, data):
        """Buscar o crear equipo"""
        # Buscar equipo existente
        equipment = request.env['inmoser.service.equipment'].sudo().search([
            ('partner_id', '=', partner.id),
            ('equipment_type', '=', data.get('equipment_type')),
            ('brand', '=', data.get('equipment_brand', '')),
            ('model', '=', data.get('equipment_model', ''))
        ], limit=1)
        
        if not equipment:
            # Crear nuevo equipo
            equipment_vals = {
                'partner_id': partner.id,
                'equipment_type': data.get('equipment_type'),
                'brand': data.get('equipment_brand', ''),
                'model': data.get('equipment_model', ''),
                'serial_number': data.get('equipment_serial', ''),
                'location': data.get('equipment_location', ''),
            }
            equipment = request.env['inmoser.service.equipment'].sudo().create(equipment_vals)
        
        return equipment
    
    @http.route(['/inmoser/api/order-status/<int:order_id>'], type='json', auth="public")
    def get_order_status(self, order_id, **kw):
        """API para obtener estado de la orden en tiempo real"""
        try:
            order = request.env['inmoser.service.order'].sudo().browse(order_id)
            
            if not order.exists():
                return {'error': 'Order not found'}
            
            return {
                'success': True,
                'order_id': order.id,
                'name': order.name,
                'state': order.state,
                'state_display': dict(order._fields['state'].selection)[order.state],
                'assigned_technician': order.assigned_technician_id.name if order.assigned_technician_id else None,
                'scheduled_date': order.scheduled_date.isoformat() if order.scheduled_date else None,
                'total_amount': order.total_amount,
                'currency': order.currency_id.symbol,
                'progress_percentage': order._get_progress_percentage(),
            }
            
        except Exception as e:
            _logger.error(f"Error getting order status: {str(e)}")
            return {'error': str(e)}
    
    @http.route(['/inmoser/api/technician-location/<int:order_id>'], type='json', auth="public")
    def get_technician_location(self, order_id, **kw):
        """API para obtener ubicación del técnico (si está disponible)"""
        try:
            order = request.env['inmoser.service.order'].sudo().browse(order_id)
            
            if not order.exists() or not order.assigned_technician_id:
                return {'error': 'Order or technician not found'}
            
            # Aquí se podría integrar con un sistema de GPS real
            # Por ahora retornamos datos simulados
            return {
                'success': True,
                'technician_name': order.assigned_technician_id.name,
                'estimated_arrival': '15 minutes',  # Esto sería calculado en tiempo real
                'is_en_route': order.state in ['assigned', 'in_progress'],
            }
            
        except Exception as e:
            _logger.error(f"Error getting technician location: {str(e)}")
            return {'error': str(e)}

class InmoserPortalExtended(CustomerPortal):
    """
    Extensión del portal de clientes de Odoo para funcionalidades de Inmoser
    """
    
    def _prepare_home_portal_values(self, counters):
        """Añadir contadores de Inmoser al portal"""
        values = super()._prepare_home_portal_values(counters)
        
        if 'service_order_count' in counters:
            partner = request.env.user.partner_id
            service_order_count = request.env['inmoser.service.order'].search_count([
                ('partner_id', '=', partner.id)
            ])
            values['service_order_count'] = service_order_count
        
        if 'equipment_count' in counters:
            partner = request.env.user.partner_id
            equipment_count = request.env['inmoser.service.equipment'].search_count([
                ('partner_id', '=', partner.id)
            ])
            values['equipment_count'] = equipment_count
        
        return values
    
    @http.route(['/my/service-orders', '/my/service-orders/page/<int:page>'], 
                type='http', auth="user", website=True)
    def portal_my_service_orders(self, page=1, date_begin=None, date_end=None, 
                                sortby=None, filterby=None, **kw):
        """Portal de órdenes de servicio del cliente"""
        values = self._prepare_portal_layout_values()
        partner = request.env.user.partner_id
        
        ServiceOrder = request.env['inmoser.service.order']
        
        domain = [('partner_id', '=', partner.id)]
        
        # Filtros de fecha
        if date_begin and date_end:
            domain += [('create_date', '>', date_begin), ('create_date', '<=', date_end)]
        
        # Filtros por estado
        if filterby == 'active':
            domain += [('state', 'not in', ['done', 'cancelled'])]
        elif filterby == 'completed':
            domain += [('state', '=', 'done')]
        
        # Ordenamiento
        order = 'create_date desc'
        if sortby == 'date':
            order = 'scheduled_date desc'
        elif sortby == 'name':
            order = 'name'
        
        # Paginación
        order_count = ServiceOrder.search_count(domain)
        pager = request.website.pager(
            url="/my/service-orders",
            url_args={'date_begin': date_begin, 'date_end': date_end, 'sortby': sortby, 'filterby': filterby},
            total=order_count,
            page=page,
            step=self._items_per_page
        )
        
        orders = ServiceOrder.search(domain, order=order, limit=self._items_per_page, offset=pager['offset'])
        
        values.update({
            'orders': orders,
            'page_name': 'service_orders',
            'pager': pager,
            'default_url': '/my/service-orders',
            'searchbar_sortings': {
                'date': {'label': _('Newest'), 'order': 'create_date desc'},
                'name': {'label': _('Name'), 'order': 'name'},
                'scheduled': {'label': _('Scheduled Date'), 'order': 'scheduled_date desc'},
            },
            'searchbar_filters': {
                'all': {'label': _('All'), 'domain': []},
                'active': {'label': _('Active'), 'domain': [('state', 'not in', ['done', 'cancelled'])]},
                'completed': {'label': _('Completed'), 'domain': [('state', '=', 'done')]},
            },
            'sortby': sortby,
            'filterby': filterby,
        })
        
        return request.render("inmoser_service_order.portal_my_service_orders", values)
    
    @http.route(['/my/service-orders/<int:order_id>'], type='http', auth="user", website=True)
    def portal_service_order_detail(self, order_id, **kw):
        """Detalle de orden de servicio en el portal"""
        try:
            order = self._document_check_access('inmoser.service.order', order_id)
        except (AccessError, MissingError):
            return request.redirect('/my')
        
        values = {
            'order': order,
            'page_name': 'service_order_detail',
        }
        
        return request.render("inmoser_service_order.portal_service_order_detail", values)

