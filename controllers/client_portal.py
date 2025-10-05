from odoo import http, _
from odoo.http import request, content_disposition
from odoo.addons.portal.controllers.portal import CustomerPortal, pager as portal_pager
from odoo.exceptions import AccessError, MissingError

class CustomerPortal(CustomerPortal):
    
    def _prepare_home_portal_values(self, counters):
        values = super()._prepare_home_portal_values(counters)
        partner = request.env.user.partner_id
        
        ServiceOrder = request.env['service.order']
        ServiceEquipment = request.env['service.equipment']
        
        if 'service_order_count' in counters:
            values['service_order_count'] = ServiceOrder.search_count([
                ('client_id', '=', partner.id)
            ]) if ServiceOrder.check_access_rights('read', raise_exception=False) else 0
        
        if 'service_equipment_count' in counters:
            values['service_equipment_count'] = ServiceEquipment.search_count([
                ('client_id', '=', partner.id)
            ]) if ServiceEquipment.check_access_rights('read', raise_exception=False) else 0
        
        return values
    
    def _service_order_get_page_view_values(self, service_order, access_token, **kwargs):
        values = {
            'page_name': 'service_order',
            'service_order': service_order,
            'user': request.env.user,
        }
        return self._get_page_view_values(service_order, access_token, values, 'my_services_history', False, **kwargs)
    
    @http.route(['/my/services', '/my/services/page/<int:page>'], type='http', auth="user", website=True)
    def portal_my_services(self, page=1, date_begin=None, date_end=None, sortby=None, search=None, search_in='all', **kw):
        values = self._prepare_portal_layout_values()
        partner = request.env.user.partner_id
        ServiceOrder = request.env['service.order']
        
        searchbar_sortings = {
            'date': {'label': _('Fecha'), 'order': 'scheduled_date desc'},
            'name': {'label': _('Número'), 'order': 'name'},
            'state': {'label': _('Estado'), 'order': 'state'},
        }
        
        searchbar_filters = {
            'all': {'label': _('Todos'), 'domain': []},
            'draft': {'label': _('Borrador'), 'domain': [('state', '=', 'draft')]},
            'confirmed': {'label': _('Confirmado'), 'domain': [('state', '=', 'confirmed')]},
            'in_progress': {'label': _('En Progreso'), 'domain': [('state', '=', 'in_progress')]},
            'done': {'label': _('Completado'), 'domain': [('state', '=', 'done')]},
            'cancel': {'label': _('Cancelado'), 'domain': [('state', '=', 'cancel')]},
        }
        
        searchbar_inputs = {
            'all': {'input': 'all', 'label': _('Buscar en todos')},
            'name': {'input': 'name', 'label': _('Buscar en Número')},
            'equipment': {'input': 'equipment', 'label': _('Buscar en Equipo')},
            'technician': {'input': 'technician', 'label': _('Buscar en Técnico')},
        }
        
        # default sort by order
        if not sortby:
            sortby = 'date'
        order = searchbar_sortings[sortby]['order']
        
        # default search by
        if search and search_in:
            search_domain = []
            if search_in == 'name':
                search_domain = [('name', 'ilike', search)]
            elif search_in == 'equipment':
                search_domain = [('equipment_id.name', 'ilike', search)]
            elif search_in == 'technician':
                search_domain = [('technician_id.name', 'ilike', search)]
            else:
                search_domain = [('name', 'ilike', search), ('description', 'ilike', search)]
        else:
            search_domain = searchbar_filters.get('all', {}).get('domain', [])
        
        # domain for partner
        domain = [('client_id', '=', partner.id)] + search_domain
        
        # count for pager
        service_order_count = ServiceOrder.search_count(domain)
        
        # pager
        pager = portal_pager(
            url="/my/services",
            url_args={'date_begin': date_begin, 'date_end': date_end, 'sortby': sortby, 'search_in': search_in, 'search': search},
            total=service_order_count,
            page=page,
            step=self._items_per_page
        )
        
        # content according to pager and archive selected
        service_orders = ServiceOrder.search(domain, order=order, limit=self._items_per_page, offset=pager['offset'])
        request.session['my_services_history'] = service_orders.ids[:100]
        
        values.update({
            'date': date_begin,
            'service_orders': service_orders,
            'page_name': 'service_order',
            'pager': pager,
            'default_url': '/my/services',
            'searchbar_sortings': searchbar_sortings,
            'searchbar_filters': searchbar_filters,
            'searchbar_inputs': searchbar_inputs,
            'sortby': sortby,
            'search_in': search_in,
            'search': search,
        })
        return request.render("inmoser_service_order.portal_my_services", values)
    
    @http.route(['/my/service/<int:service_order_id>'], type='http', auth="public", website=True)
    def portal_my_service_order(self, service_order_id=None, access_token=None, **kw):
        try:
            service_order_sudo = self._document_check_access('service.order', service_order_id, access_token)
        except (AccessError, MissingError):
            return request.redirect('/my')
        
        values = self._service_order_get_page_view_values(service_order_sudo, access_token, **kw)
        return request.render("inmoser_service_order.portal_my_service", values)
    
    @http.route(['/my/equipments', '/my/equipments/page/<int:page>'], type='http', auth="user", website=True)
    def portal_my_equipments(self, page=1, date_begin=None, date_end=None, sortby=None, **kw):
        values = self._prepare_portal_layout_values()
        partner = request.env.user.partner_id
        ServiceEquipment = request.env['service.equipment']
        
        searchbar_sortings = {
            'name': {'label': _('Nombre'), 'order': 'name'},
            'serial': {'label': _('Serie'), 'order': 'serial_number'},
            'type': {'label': _('Tipo'), 'order': 'equipment_type_id'},
        }
        
        # default sort by order
        if not sortby:
            sortby = 'name'
        order = searchbar_sortings[sortby]['order']
        
        # domain for partner
        domain = [('client_id', '=', partner.id)]
        
        # count for pager
        equipment_count = ServiceEquipment.search_count(domain)
        
        # pager
        pager = portal_pager(
            url="/my/equipments",
            url_args={'date_begin': date_begin, 'date_end': date_end, 'sortby': sortby},
            total=equipment_count,
            page=page,
            step=self._items_per_page
        )
        
        # content according to pager and archive selected
        equipments = ServiceEquipment.search(domain, order=order, limit=self._items_per_page, offset=pager['offset'])
        request.session['my_equipments_history'] = equipments.ids[:100]
        
        values.update({
            'date': date_begin,
            'equipments': equipments,
            'page_name': 'equipment',
            'pager': pager,
            'default_url': '/my/equipments',
            'searchbar_sortings': searchbar_sortings,
            'sortby': sortby,
        })
        return request.render("inmoser_service_order.portal_my_equipments", values)
    
    @http.route(['/my/equipment/<int:equipment_id>'], type='http', auth="public", website=True)
    def portal_my_equipment(self, equipment_id=None, access_token=None, **kw):
        try:
            equipment_sudo = self._document_check_access('service.equipment', equipment_id, access_token)
        except (AccessError, MissingError):
            return request.redirect('/my')
        
        values = {
            'equipment': equipment_sudo,
            'page_name': 'equipment',
            'user': request.env.user,
        }
        return request.render("inmoser_service_order.portal_my_equipment", values)
    
    @http.route(['/my/service/<int:service_order_id>/pdf'], type='http', auth="public", website=True)
    def portal_my_service_order_report(self, service_order_id=None, access_token=None, **kw):
        try:
            service_order_sudo = self._document_check_access('service.order', service_order_id, access_token)
        except (AccessError, MissingError):
            return request.redirect('/my')
        
        # print report as html
        if 'report_type' in request.params and request.params['report_type'] == 'html':
            return request.render('inmoser_service_order.report_service_order', {
                'docids': service_order_sudo.ids,
                'doc_model': 'service.order',
                'docs': service_order_sudo,
            })
        
        # print report as pdf
        pdf = request.env.ref('inmoser_service_order.action_report_service_order').sudo().render_qweb_pdf([service_order_sudo.id])
        pdfhttpheaders = [
            ('Content-Type', 'application/pdf'),
            ('Content-Length', len(pdf)),
        ]
        return request.make_response(pdf, headers=pdfhttpheaders)
    
    @http.route(['/my/service/new'], type='http', auth="user", website=True)
    def portal_new_service_order(self, **kw):
        partner = request.env.user.partner_id
        
        # Obtener equipos del cliente
        equipments = request.env['service.equipment'].search([('client_id', '=', partner.id)])
        
        # Obtener tipos de servicio
        service_types = request.env['service.type'].search([('active', '=', True)])
        
        # Obtener técnicos
        technicians = request.env['hr.employee'].search([('is_technician', '=', True)])
        
        values = {
            'equipments': equipments,
            'service_types': service_types,
            'technicians': technicians,
            'page_name': 'new_service_order',
        }
        
        if request.httprequest.method == 'POST':
            # Procesar formulario
            service_order_data = {
                'client_id': partner.id,
                'equipment_id': int(kw.get('equipment_id')),
                'service_type_id': int(kw.get('service_type_id')),
                'technician_id': int(kw.get('technician_id')) if kw.get('technician_id') else False,
                'scheduled_date': kw.get('scheduled_date'),
                'description': kw.get('description'),
                'custom_sale_type': kw.get('custom_sale_type', 'service'),
                'priority': kw.get('priority', '0'),
            }
            
            try:
                service_order = request.env['service.order'].create(service_order_data)
                return request.redirect(f'/my/service/{service_order.id}')
            except Exception as e:
                values['error'] = str(e)
                values['form_data'] = kw
        
        return request.render("inmoser_service_order.portal_new_service_order", values)
    
    @http.route(['/my/service/<int:service_order_id>/cancel'], type='http', auth="user", website=True)
    def portal_cancel_service_order(self, service_order_id, **kw):
        try:
            service_order = request.env['service.order'].browse(service_order_id)
            if service_order.client_id != request.env.user.partner_id:
                raise AccessError(_('No tiene permiso para cancelar esta orden de servicio'))
            
            if service_order.state in ['draft', 'confirmed']:
                service_order.action_cancel_service()
                return request.redirect(f'/my/service/{service_order_id}')
            else:
                return request.redirect(f'/my/service/{service_order_id}?error=No se puede cancelar esta orden')
        except Exception as e:
            return request.redirect(f'/my/service/{service_order_id}?error={str(e)}')
