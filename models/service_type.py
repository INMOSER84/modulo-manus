# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class ServiceType(models.Model):
    _name = 'inmoser.service.type'
    _description = 'Service Type'
    _order = 'sequence, name'
    _rec_name = 'name'

    # Campos básicos
    name = fields.Char(
        string='Service Type Name',
        help='Nombre del tipo de servicio',
        required=True,
        translate=True
    )
    
    description = fields.Text(
        string='Description',
        help='Descripción detallada del tipo de servicio',
        translate=True
    )
    
    # Configuración visual
    template_image = fields.Binary(
        string='Template Image',
        help='Imagen de plantilla para personalización del formato de la OS'
    )
    
    color = fields.Integer(
        string='Color',
        help='Color para identificación visual en interfaces'
    )
    
    # Control y organización
    active = fields.Boolean(
        string='Active',
        default=True,
        help='Si está desmarcado, el tipo de servicio no aparecerá en las búsquedas'
    )
    
    sequence = fields.Integer(
        string='Sequence',
        default=10,
        help='Orden de visualización en listas'
    )
    
    # Configuración de servicio
    estimated_duration = fields.Float(
        string='Estimated Duration (Hours)',
        help='Duración estimada del servicio en horas',
        default=2.0
    )
    
    requires_diagnosis = fields.Boolean(
        string='Requires Diagnosis',
        help='Indica si este tipo de servicio requiere diagnóstico previo',
        default=True
    )
    
    requires_approval = fields.Boolean(
        string='Requires Customer Approval',
        help='Indica si requiere aprobación del cliente antes de proceder',
        default=True
    )
    
    allow_photos = fields.Boolean(
        string='Allow Photos',
        help='Permite tomar fotos antes y después del servicio',
        default=True
    )
    
    # Configuración de precios
    base_price = fields.Float(
        string='Base Price',
        help='Precio base para este tipo de servicio',
        default=0.0
    )
    
    currency_id = fields.Many2one(
        'res.currency',
        string='Currency',
        default=lambda self: self.env.company.currency_id
    )
    
    # Configuración de inventario
    default_product_ids = fields.Many2many(
        'product.product',
        'service_type_product_rel',
        'service_type_id',
        'product_id',
        string='Default Products',
        help='Productos/refacciones comúnmente utilizados en este tipo de servicio'
    )
    
    # Relaciones
    service_order_ids = fields.One2many(
        'inmoser.service.order',
        'service_type_id',
        string='Service Orders',
        help='Órdenes de servicio de este tipo'
    )
    
    # Campos computados
    service_order_count = fields.Integer(
        string='Service Orders Count',
        compute='_compute_service_order_count',
        help='Número total de órdenes de servicio de este tipo'
    )
    
    avg_completion_time = fields.Float(
        string='Average Completion Time',
        compute='_compute_avg_completion_time',
        help='Tiempo promedio de completación en horas'
    )

    @api.depends('service_order_ids')
    def _compute_service_order_count(self):
        """Calcula el número de órdenes de servicio de este tipo"""
        for service_type in self:
            service_type.service_order_count = len(service_type.service_order_ids)

    @api.depends('service_order_ids.scheduled_date', 'service_order_ids.write_date', 'service_order_ids.state')
    def _compute_avg_completion_time(self):
        """Calcula el tiempo promedio de completación"""
        for service_type in self:
            completed_orders = service_type.service_order_ids.filtered(
                lambda o: o.state == 'done' and o.scheduled_date and o.write_date
            )
            
            if completed_orders:
                total_hours = 0
                count = 0
                
                for order in completed_orders:
                    # Calcular diferencia en horas entre inicio programado y finalización
                    start_time = order.scheduled_date
                    end_time = order.write_date
                    
                    if start_time and end_time:
                        diff = end_time - start_time
                        hours = diff.total_seconds() / 3600
                        total_hours += hours
                        count += 1
                
                service_type.avg_completion_time = total_hours / count if count > 0 else 0
            else:
                service_type.avg_completion_time = 0

    @api.constrains('estimated_duration')
    def _check_estimated_duration(self):
        """Valida que la duración estimada sea positiva"""
        for service_type in self:
            if service_type.estimated_duration <= 0:
                raise ValidationError(_('La duración estimada debe ser mayor que cero.'))

    @api.constrains('base_price')
    def _check_base_price(self):
        """Valida que el precio base no sea negativo"""
        for service_type in self:
            if service_type.base_price < 0:
                raise ValidationError(_('El precio base no puede ser negativo.'))

    def action_view_service_orders(self):
        """Acción para ver las órdenes de servicio de este tipo"""
        self.ensure_one()
        action = self.env.ref('inmoser_service_order.action_service_order').read()[0]
        action['domain'] = [('service_type_id', '=', self.id)]
        action['context'] = {
            'default_service_type_id': self.id,
            'search_default_service_type_id': self.id,
        }
        return action

    def get_default_products_domain(self):
        """Obtiene el dominio para productos por defecto de este tipo de servicio"""
        self.ensure_one()
        if self.default_product_ids:
            return [('id', 'in', self.default_product_ids.ids)]
        return []

    @api.model
    def get_service_types_for_equipment(self, equipment_type=None):
        """
        Obtiene tipos de servicio recomendados para un tipo de equipo
        
        Args:
            equipment_type (str): Tipo de equipo
            
        Returns:
            recordset: Tipos de servicio recomendados
        """
        # Por ahora retorna todos los tipos activos
        # En el futuro se puede implementar lógica específica por tipo de equipo
        return self.search([('active', '=', True)])

    def copy(self, default=None):
        """Override copy para añadir sufijo al nombre"""
        default = dict(default or {})
        if 'name' not in default:
            default['name'] = _('%s (Copy)') % self.name
        return super(ServiceType, self).copy(default)

    @api.model
    def create_default_service_types(self):
        """Método para crear tipos de servicio por defecto"""
        default_types = [
            {
                'name': _('Repair'),
                'description': _('Equipment repair service'),
                'estimated_duration': 3.0,
                'requires_diagnosis': True,
                'requires_approval': True,
                'sequence': 10,
            },
            {
                'name': _('Maintenance'),
                'description': _('Preventive maintenance service'),
                'estimated_duration': 2.0,
                'requires_diagnosis': False,
                'requires_approval': False,
                'sequence': 20,
            },
            {
                'name': _('Installation'),
                'description': _('Equipment installation service'),
                'estimated_duration': 4.0,
                'requires_diagnosis': False,
                'requires_approval': True,
                'sequence': 30,
            },
            {
                'name': _('Inspection'),
                'description': _('Equipment inspection and evaluation'),
                'estimated_duration': 1.0,
                'requires_diagnosis': True,
                'requires_approval': False,
                'sequence': 40,
            },
        ]
        
        for type_data in default_types:
            existing = self.search([('name', '=', type_data['name'])], limit=1)
            if not existing:
                self.create(type_data)

    def name_get(self):
        """Personaliza la visualización del nombre del tipo de servicio"""
        result = []
        for service_type in self:
            name = service_type.name or ''
            if service_type.estimated_duration:
                name += f" ({service_type.estimated_duration}h)"
            result.append((service_type.id, name))
        return result

