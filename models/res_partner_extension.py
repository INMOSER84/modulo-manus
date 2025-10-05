# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
import re


class ResPartnerExtension(models.Model):
    _inherit = 'res.partner'

    # Campos específicos para clientes de servicio
    x_inmoser_client_sequence = fields.Char(
        string='Client Sequence',
        help='Secuencia automática única para clientes de servicio (CLI00001)',
        readonly=True,
        copy=False,
        index=True
    )
    
    x_inmoser_phone_mobile_2 = fields.Char(
        string='Mobile Phone 2',
        help='Teléfono celular adicional del cliente'
    )
    
    x_inmoser_is_service_client = fields.Boolean(
        string='Is Service Client',
        help='Indica si este contacto es un cliente de servicios Inmoser',
        default=False
    )
    
    x_inmoser_client_notes = fields.Text(
        string='Client Notes',
        help='Notas adicionales específicas del cliente de servicios'
    )
    
    # Relaciones con otros modelos
    x_inmoser_equipment_ids = fields.One2many(
        'inmoser.service.equipment',
        'partner_id',
        string='Equipment',
        help='Equipos registrados para este cliente'
    )
    
    x_inmoser_service_order_ids = fields.One2many(
        'inmoser.service.order',
        'partner_id',
        string='Service Orders',
        help='Órdenes de servicio de este cliente'
    )
    
    # Campos computados
    x_inmoser_equipment_count = fields.Integer(
        string='Equipment Count',
        compute='_compute_equipment_count',
        help='Número total de equipos registrados'
    )
    
    x_inmoser_service_order_count = fields.Integer(
        string='Service Orders Count',
        compute='_compute_service_order_count',
        help='Número total de órdenes de servicio'
    )

    @api.depends('x_inmoser_equipment_ids')
    def _compute_equipment_count(self):
        """Calcula el número de equipos del cliente"""
        for partner in self:
            partner.x_inmoser_equipment_count = len(partner.x_inmoser_equipment_ids)

    @api.depends('x_inmoser_service_order_ids')
    def _compute_service_order_count(self):
        """Calcula el número de órdenes de servicio del cliente"""
        for partner in self:
            partner.x_inmoser_service_order_count = len(partner.x_inmoser_service_order_ids)

    @api.model
    def create(self, vals):
        """Override create para generar secuencia automática si es cliente de servicio"""
        if vals.get('x_inmoser_is_service_client', False) and not vals.get('x_inmoser_client_sequence'):
            vals['x_inmoser_client_sequence'] = self.env['ir.sequence'].next_by_code('inmoser.client.sequence')
        return super(ResPartnerExtension, self).create(vals)

    def write(self, vals):
        """Override write para generar secuencia si se marca como cliente de servicio"""
        if vals.get('x_inmoser_is_service_client', False):
            for partner in self:
                if not partner.x_inmoser_client_sequence:
                    vals['x_inmoser_client_sequence'] = self.env['ir.sequence'].next_by_code('inmoser.client.sequence')
        return super(ResPartnerExtension, self).write(vals)

    @api.constrains('x_inmoser_phone_mobile_2')
    def _check_phone_mobile_2_format(self):
        """Valida el formato del teléfono móvil adicional"""
        for partner in self:
            if partner.x_inmoser_phone_mobile_2:
                # Validación básica de formato de teléfono (números, espacios, guiones, paréntesis, +)
                phone_pattern = r'^[\+]?[0-9\s\-\(\)]+$'
                if not re.match(phone_pattern, partner.x_inmoser_phone_mobile_2):
                    raise ValidationError(_('El formato del teléfono móvil adicional no es válido.'))

    def action_view_equipment(self):
        """Acción para ver los equipos del cliente"""
        self.ensure_one()
        action = self.env.ref('inmoser_service_order.action_service_equipment').read()[0]
        action['domain'] = [('partner_id', '=', self.id)]
        action['context'] = {
            'default_partner_id': self.id,
            'search_default_partner_id': self.id,
        }
        return action

    def action_view_service_orders(self):
        """Acción para ver las órdenes de servicio del cliente"""
        self.ensure_one()
        action = self.env.ref('inmoser_service_order.action_service_order').read()[0]
        action['domain'] = [('partner_id', '=', self.id)]
        action['context'] = {
            'default_partner_id': self.id,
            'search_default_partner_id': self.id,
        }
        return action

    def action_create_service_order(self):
        """Acción para crear una nueva orden de servicio para este cliente"""
        self.ensure_one()
        action = self.env.ref('inmoser_service_order.action_service_order').read()[0]
        action['views'] = [(self.env.ref('inmoser_service_order.view_service_order_form').id, 'form')]
        action['context'] = {
            'default_partner_id': self.id,
        }
        return action

    @api.model
    def name_search(self, name='', args=None, operator='ilike', limit=100):
        """Extiende la búsqueda por nombre para incluir la secuencia del cliente"""
        args = args or []
        if name:
            # Buscar por secuencia de cliente también
            sequence_partners = self.search([('x_inmoser_client_sequence', operator, name)] + args, limit=limit)
            if sequence_partners:
                return sequence_partners.name_get()
        return super(ResPartnerExtension, self).name_search(name, args, operator, limit)

    def name_get(self):
        """Personaliza la visualización del nombre para incluir la secuencia si es cliente de servicio"""
        result = []
        for partner in self:
            name = partner.name or ''
            if partner.x_inmoser_is_service_client and partner.x_inmoser_client_sequence:
                name = f"[{partner.x_inmoser_client_sequence}] {name}"
            result.append((partner.id, name))
        return result

