odoo.define('inmoser_service_order.calendar_view', function (require) {
'use strict';

var CalendarView = require('web.CalendarView');
var CalendarController = require('web.CalendarController');
var CalendarRenderer = require('web.CalendarRenderer');
var core = require('web.core');
var Dialog = require('web.Dialog');
var framework = require('web.framework');
var session = require('web.session');

var _t = core._t;

/**
 * Controlador personalizado para el calendario de técnicos
 */
var TechnicianCalendarController = CalendarController.extend({
    
    /**
     * Inicializar controlador
     */
    init: function () {
        this._super.apply(this, arguments);
        this.isTechnician = false;
        this.currentTechnicianId = null;
    },
    
    /**
     * Iniciar controlador
     */
    start: function () {
        var self = this;
        return this._super.apply(this, arguments).then(function () {
            return self._checkTechnicianRole();
        });
    },
    
    /**
     * Verificar si el usuario actual es técnico
     */
    _checkTechnicianRole: function () {
        var self = this;
        return this._rpc({
            model: 'hr.employee',
            method: 'search_read',
            args: [[['user_id', '=', session.uid], ['x_inmoser_is_technician', '=', true]]],
            fields: ['id', 'name']
        }).then(function (result) {
            if (result.length > 0) {
                self.isTechnician = true;
                self.currentTechnicianId = result[0].id;
                self._addTechnicianFilters();
            }
        });
    },
    
    /**
     * Añadir filtros específicos para técnicos
     */
    _addTechnicianFilters: function () {
        if (this.isTechnician) {
            // Filtrar automáticamente por técnico actual
            var domain = [['assigned_technician_id', '=', this.currentTechnicianId]];
            this.renderer.state.domain = domain;
            this.reload();
        }
    },
    
    /**
     * Manejar clic en evento del calendario
     */
    _onCalendarEventClick: function (event) {
        var self = this;
        var eventId = event.data.id;
        
        if (this.isTechnician) {
            this._openTechnicianServiceDialog(eventId);
        } else {
            this._super.apply(this, arguments);
        }
    },
    
    /**
     * Abrir diálogo específico para técnicos
     */
    _openTechnicianServiceDialog: function (serviceOrderId) {
        var self = this;
        
        // Obtener datos de la orden de servicio
        this._rpc({
            model: 'inmoser.service.order',
            method: 'read',
            args: [serviceOrderId, [
                'name', 'partner_id', 'equipment_id', 'service_type_id',
                'scheduled_date', 'state', 'reported_fault', 'diagnosis',
                'work_performed', 'total_amount', 'currency_id'
            ]]
        }).then(function (result) {
            if (result.length > 0) {
                var order = result[0];
                self._showTechnicianDialog(order);
            }
        });
    },
    
    /**
     * Mostrar diálogo para técnicos
     */
    _showTechnicianDialog: function (order) {
        var self = this;
        
        var $content = $(core.qweb.render('inmoser_service_order.TechnicianServiceDialog', {
            order: order
        }));
        
        var dialog = new Dialog(this, {
            title: _t('Service Order: ') + order.name,
            size: 'large',
            $content: $content,
            buttons: this._getTechnicianDialogButtons(order)
        });
        
        dialog.open();
        
        // Añadir funcionalidad a los botones
        dialog.$modal.find('.btn-start-service').click(function () {
            self._startService(order.id);
            dialog.close();
        });
        
        dialog.$modal.find('.btn-navigate').click(function () {
            self._navigateToCustomer(order);
        });
        
        dialog.$modal.find('.btn-complete-service').click(function () {
            self._completeService(order.id);
            dialog.close();
        });
    },
    
    /**
     * Obtener botones del diálogo según el estado
     */
    _getTechnicianDialogButtons: function (order) {
        var buttons = [];
        
        if (order.state === 'assigned') {
            buttons.push({
                text: _t('Start Service'),
                classes: 'btn-primary btn-start-service',
                close: false
            });
        }
        
        if (order.state === 'in_progress') {
            buttons.push({
                text: _t('Complete Service'),
                classes: 'btn-success btn-complete-service',
                close: false
            });
        }
        
        buttons.push({
            text: _t('Navigate to Customer'),
            classes: 'btn-info btn-navigate',
            close: false
        });
        
        buttons.push({
            text: _t('Close'),
            classes: 'btn-secondary',
            close: true
        });
        
        return buttons;
    },
    
    /**
     * Iniciar servicio
     */
    _startService: function (serviceOrderId) {
        var self = this;
        
        this._rpc({
            model: 'inmoser.service.order',
            method: 'action_start_service',
            args: [serviceOrderId]
        }).then(function () {
            self.displayNotification({
                type: 'success',
                message: _t('Service started successfully')
            });
            self.reload();
        }).catch(function (error) {
            self.displayNotification({
                type: 'danger',
                message: error.message || _t('Error starting service')
            });
        });
    },
    
    /**
     * Navegar al cliente usando Google Maps
     */
    _navigateToCustomer: function (order) {
        var address = '';
        
        // Construir dirección del cliente
        if (order.partner_id && order.partner_id[0]) {
            this._rpc({
                model: 'res.partner',
                method: 'read',
                args: [order.partner_id[0], ['street', 'city', 'state_id', 'country_id']]
            }).then(function (result) {
                if (result.length > 0) {
                    var partner = result[0];
                    var addressParts = [];
                    
                    if (partner.street) addressParts.push(partner.street);
                    if (partner.city) addressParts.push(partner.city);
                    if (partner.state_id) addressParts.push(partner.state_id[1]);
                    if (partner.country_id) addressParts.push(partner.country_id[1]);
                    
                    address = addressParts.join(', ');
                    
                    if (address) {
                        var mapsUrl = 'https://www.google.com/maps/dir/?api=1&destination=' + 
                                     encodeURIComponent(address);
                        window.open(mapsUrl, '_blank');
                    } else {
                        alert(_t('Customer address not available'));
                    }
                }
            });
        }
    },
    
    /**
     * Completar servicio
     */
    _completeService: function (serviceOrderId) {
        var self = this;
        
        // Abrir wizard de completar servicio
        this.do_action({
            type: 'ir.actions.act_window',
            res_model: 'inmoser.service.complete.wizard',
            view_mode: 'form',
            view_type: 'form',
            views: [[false, 'form']],
            target: 'new',
            context: {
                default_service_order_id: serviceOrderId
            }
        });
    }
});

/**
 * Renderer personalizado para el calendario
 */
var TechnicianCalendarRenderer = CalendarRenderer.extend({
    
    /**
     * Personalizar colores de eventos según estado
     */
    _getEventColor: function (event) {
        var state = event.record.state;
        var colors = {
            'draft': '#6c757d',      // Gris
            'assigned': '#007bff',    // Azul
            'in_progress': '#28a745', // Verde
            'pending_approval': '#ffc107', // Amarillo
            'accepted': '#17a2b8',    // Cyan
            'done': '#28a745',        // Verde oscuro
            'cancelled': '#dc3545'    // Rojo
        };
        
        return colors[state] || '#007bff';
    },
    
    /**
     * Personalizar texto del evento
     */
    _getEventTitle: function (event) {
        var record = event.record;
        var title = record.name || '';
        
        if (record.partner_id) {
            title += ' - ' + record.partner_id[1];
        }
        
        if (record.equipment_id) {
            title += ' (' + record.equipment_id[1] + ')';
        }
        
        return title;
    }
});

/**
 * Vista personalizada del calendario
 */
var TechnicianCalendarView = CalendarView.extend({
    config: _.extend({}, CalendarView.prototype.config, {
        Controller: TechnicianCalendarController,
        Renderer: TechnicianCalendarRenderer,
    }),
});

// Registrar la vista
core.view_registry.add('technician_calendar', TechnicianCalendarView);

return {
    TechnicianCalendarView: TechnicianCalendarView,
    TechnicianCalendarController: TechnicianCalendarController,
    TechnicianCalendarRenderer: TechnicianCalendarRenderer,
};

});

