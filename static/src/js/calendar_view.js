/** @odoo-module **/

import { CalendarController } from "@web/views/calendar/calendar_controller";
import { CalendarRenderer } from "@web/views/calendar/calendar_renderer";
import { CalendarModel } from "@web/views/calendar/calendar_model";
import { viewRegistry } from "@web/core/registry";
import { _t } from "@web/core/l10n/translation";
import { useService } from "@web/core/utils/hooks";

export class ServiceCalendarRenderer extends CalendarRenderer {
    /**
     * Override para personalizar la vista de calendario
     */
    onEventRendered(event) {
        super.onEventRendered(...arguments);
        
        // Añadir clase según el estado
        if (event.record.state) {
            event.el.classList.add('o_calendar_service_' + event.record.state);
        }

        // Añadir prioridad
        if (event.record.priority && event.record.priority !== '0') {
            event.el.classList.add('o_calendar_priority_' + event.record.priority);
        }
    }

    /**
     * Personalizar popover del evento
     */
    getEventPopoverTemplate() {
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
}

export class ServiceCalendarModel extends CalendarModel {
    setup() {
        super.setup();
        this.orm = useService("orm");
    }

    /**
     * Override para cargar datos adicionales
     */
    async loadData(params) {
        await super.loadData(...arguments);
        // Cargar información adicional para los eventos
        await this._loadAdditionalInfo();
    }

    async _loadAdditionalInfo() {
        const service_ids = this.data.records.map(record => record.id);

        if (service_ids.length === 0) {
            return;
        }

        const results = await this.orm.call(
            'service.order',
            'read',
            [service_ids, ['client_id', 'equipment_id', 'service_type_id', 'technician_id', 'priority']]
        );

        const additional_info = {};
        results.forEach(service => {
            additional_info[service.id] = {
                client_id: service.client_id,
                equipment_id: service.equipment_id,
                service_type_id: service.service_type_id,
                technician_id: service.technician_id,
                priority: service.priority,
            };
        });

        this.data.records.forEach(event => {
            Object.assign(event, additional_info[event.id] || {});
        });
    }
}

export class ServiceCalendarController extends CalendarController {
    setup() {
        super.setup();
        // Puedes agregar configuraciones adicionales aquí
    }
}

export const ServiceCalendarView = {
    type: "calendar",
    display_name: _t("Service Calendar"),
    icon: "fa-calendar",
    Model: ServiceCalendarModel,
    Renderer: ServiceCalendarRenderer,
    Controller: ServiceCalendarController,
    props: (props, view) => {
        const { archInfo, ...viewProps } = props;
        return {
            ...viewProps,
            Model: ServiceCalendarModel,
            Renderer: ServiceCalendarRenderer,
            buttonTemplate: "CalendarView.buttons",
            archInfo: {
                ...archInfo,
                hasCreate: true,
                hasEdit: true,
            },
        };
    },
};

viewRegistry.add("service_calendar", ServiceCalendarView);
