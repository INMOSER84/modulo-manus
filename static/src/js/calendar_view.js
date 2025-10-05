odoo.define('inmoser_service_order.calendar_view', function (require) {
    "use strict";
    
    var core = require('web.core');
    var CalendarView = require('web.CalendarView');
    var CalendarRenderer = require('web.CalendarRenderer');
    var CalendarModel = require('web.CalendarModel');
    var viewRegistry = require('web.view_registry');
    
    var _t = core._t;
    
    var ServiceCalendarRenderer = CalendarRenderer.extend({
        /**
         * Override para personalizar la vista de calendario
         */
        _renderEvent: function (event) {
            var $event = this._super.apply(this, arguments);
            
            // Añadir clase según el estado
            if (event.state) {
                $event.addClass('o_calendar_service_' + event.state);
            }
            
            // Añadir prioridad
            if (event.priority && event.priority !== '0') {
                $event.addClass('o_calendar_priority_' + event.priority);
            }
            
            return $event;
        },
        
        /**
         * Personalizar popover del evento
         */
        _getEventTemplate: function () {
            return '' +
                '<div class="o_calendar_service_popover">' +
                '  <div class="popover-arrow"></div>' +
                '  <h3 class="popover-title"></h3>' +
                '  <div class="popover-content">' +
                '    <div class="o_service_info">' +
                '      <div class="o_service_client"><strong>Cliente:</strong> <span class="o_service_client_value"/></div>' +
                '      <div class="o_service_equipment"><strong>Equipo:</strong> <span class="o_service_equipment_value"/></div>' +
                '      <div class="o_service_type"><strong>Tipo:</strong> <span class="o_service_type_value"/></div>' +
                '      <div class="o_service_technician"><strong>Técnico:</strong> <span class="o_service_technician_value"/></div>' +
                '      <div class="o_service_priority"><strong>Prioridad:</strong> <span class="o_service_priority_value"/></div>' +
                '    </div>' +
                '  </div>' +
                '</div>';
        }
    });
    
    var ServiceCalendarModel = CalendarModel.extend({
        /**
         * Override para cargar datos adicionales
         */
        loadData: function () {
            var self = this;
            return this._super.apply(this, arguments).then(function () {
                // Cargar información adicional para los eventos
                return self._loadAdditionalInfo();
            });
        },
        
        _loadAdditionalInfo: function () {
            var self = this;
            var service_ids = this.data.map(function (event) {
                return event.id;
            });
            
            if (service_ids.length === 0) {
                return $.when();
            }
            
            return this._rpc({
                model: 'service.order',
                method: 'read',
                args: [service_ids, ['client_id', 'equipment_id', 'service_type_id', 'technician_id', 'priority']],
            }).then(function (results) {
                var additional_info = {};
                results.forEach(function (service) {
                    additional_info[service.id] = {
                        client_id: service.client_id,
                        equipment_id: service.equipment_id,
                        service_type_id: service.service_type_id,
                        technician_id: service.technician_id,
                        priority: service.priority,
                    };
                });
                
                self.data.forEach(function (event) {
                    _.extend(event, additional_info[event.id] || {});
                });
            });
        }
    });
    
    var ServiceCalendarView = CalendarView.extend({
        config: _.extend({}, CalendarView.prototype.config, {
            Model: ServiceCalendarModel,
            Renderer: ServiceCalendarRenderer,
        }),
    });
    
    viewRegistry.add('service_calendar', ServiceCalendarView);
    
    return {
        ServiceCalendarRenderer: ServiceCalendarRenderer,
        ServiceCalendarModel: ServiceCalendarModel,
        ServiceCalendarView: ServiceCalendarView,
    };
});
