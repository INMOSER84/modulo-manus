# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
import logging

_logger = logging.getLogger(__name__)

class ServiceOrderAccountingIntegration(models.Model):
    """
    Integración del módulo de órdenes de servicio con contabilidad
    """
    _inherit = 'inmoser.service.order'
    
    # Campos de integración contable
    invoice_id = fields.Many2one(
        'account.move',
        string='Invoice',
        readonly=True,
        help='Invoice generated for this service order'
    )
    
    invoice_status = fields.Selection([
        ('no', 'Nothing to Invoice'),
        ('to_invoice', 'To Invoice'),
        ('invoiced', 'Fully Invoiced'),
    ], string='Invoice Status', compute='_compute_invoice_status', store=True)
    
    payment_status = fields.Selection([
        ('not_paid', 'Not Paid'),
        ('partial', 'Partially Paid'),
        ('paid', 'Fully Paid'),
    ], string='Payment Status', compute='_compute_payment_status', store=True)
    
    journal_entry_id = fields.Many2one(
        'account.move',
        string='Journal Entry',
        readonly=True,
        help='Accounting entry for service revenue'
    )
    
    @api.depends('invoice_id', 'invoice_id.payment_state')
    def _compute_invoice_status(self):
        """Calcular estado de facturación"""
        for order in self:
            if not order.invoice_id:
                if order.state == 'done' and order.total_amount > 0:
                    order.invoice_status = 'to_invoice'
                else:
                    order.invoice_status = 'no'
            else:
                order.invoice_status = 'invoiced'
    
    @api.depends('invoice_id', 'invoice_id.payment_state')
    def _compute_payment_status(self):
        """Calcular estado de pago"""
        for order in self:
            if not order.invoice_id:
                order.payment_status = 'not_paid'
            else:
                if order.invoice_id.payment_state == 'paid':
                    order.payment_status = 'paid'
                elif order.invoice_id.payment_state == 'partial':
                    order.payment_status = 'partial'
                else:
                    order.payment_status = 'not_paid'
    
    def action_create_invoice(self):
        """Crear factura para la orden de servicio"""
        self.ensure_one()
        
        if self.invoice_id:
            raise UserError(_('Invoice already exists for this service order.'))
        
        if self.state != 'done':
            raise UserError(_('Only completed service orders can be invoiced.'))
        
        if self.total_amount <= 0:
            raise UserError(_('Cannot create invoice with zero amount.'))
        
        # Crear factura
        invoice_vals = self._prepare_invoice_vals()
        invoice = self.env['account.move'].create(invoice_vals)
        
        # Crear líneas de factura
        self._create_invoice_lines(invoice)
        
        # Vincular factura
        self.invoice_id = invoice.id
        
        # Registrar en el chatter
        self.message_post(
            body=_('Invoice %s created for service order %s') % (invoice.name, self.name),
            message_type='notification'
        )
        
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'account.move',
            'res_id': invoice.id,
            'view_mode': 'form',
            'target': 'current',
        }
    
    def _prepare_invoice_vals(self):
        """Preparar valores para la factura"""
        return {
            'move_type': 'out_invoice',
            'partner_id': self.partner_id.id,
            'invoice_date': fields.Date.today(),
            'invoice_origin': self.name,
            'ref': self.name,
            'narration': _('Service Order: %s\nEquipment: %s\nService Type: %s') % (
                self.name,
                self.equipment_id.name,
                self.service_type_id.name
            ),
            'company_id': self.company_id.id,
            'currency_id': self.currency_id.id,
        }
    
    def _create_invoice_lines(self, invoice):
        """Crear líneas de la factura"""
        # Línea principal del servicio
        service_line_vals = {
            'move_id': invoice.id,
            'name': _('Service: %s - %s') % (self.service_type_id.name, self.equipment_id.name),
            'quantity': 1,
            'price_unit': self.service_type_id.base_price,
            'account_id': self._get_service_account().id,
        }
        
        self.env['account.move.line'].create(service_line_vals)
        
        # Líneas de refacciones
        for refaction_line in self.refaction_line_ids:
            refaction_line_vals = {
                'move_id': invoice.id,
                'product_id': refaction_line.product_id.id,
                'name': refaction_line.description or refaction_line.product_id.name,
                'quantity': refaction_line.quantity,
                'price_unit': refaction_line.unit_price,
                'account_id': refaction_line.product_id.property_account_income_id.id or 
                             refaction_line.product_id.categ_id.property_account_income_categ_id.id,
            }
            
            self.env['account.move.line'].create(refaction_line_vals)
    
    def _get_service_account(self):
        """Obtener cuenta contable para servicios"""
        # Buscar cuenta de ingresos por servicios
        service_account = self.env['account.account'].search([
            ('code', 'like', '7%'),  # Cuentas de ingresos
            ('name', 'ilike', 'service'),
            ('company_id', '=', self.company_id.id)
        ], limit=1)
        
        if not service_account:
            # Usar cuenta de ingresos por defecto
            service_account = self.env['account.account'].search([
                ('user_type_id.name', '=', 'Income'),
                ('company_id', '=', self.company_id.id)
            ], limit=1)
        
        if not service_account:
            raise UserError(_('No income account found. Please configure accounting properly.'))
        
        return service_account
    
    def action_create_journal_entry(self):
        """Crear asiento contable para el servicio"""
        self.ensure_one()
        
        if self.journal_entry_id:
            raise UserError(_('Journal entry already exists for this service order.'))
        
        if self.state != 'done':
            raise UserError(_('Only completed service orders can generate journal entries.'))
        
        # Crear asiento contable
        journal_entry_vals = self._prepare_journal_entry_vals()
        journal_entry = self.env['account.move'].create(journal_entry_vals)
        
        # Crear líneas del asiento
        self._create_journal_entry_lines(journal_entry)
        
        # Vincular asiento
        self.journal_entry_id = journal_entry.id
        
        # Confirmar asiento
        journal_entry.action_post()
        
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'account.move',
            'res_id': journal_entry.id,
            'view_mode': 'form',
            'target': 'current',
        }
    
    def _prepare_journal_entry_vals(self):
        """Preparar valores para el asiento contable"""
        return {
            'move_type': 'entry',
            'date': fields.Date.today(),
            'ref': self.name,
            'journal_id': self._get_service_journal().id,
            'company_id': self.company_id.id,
        }
    
    def _create_journal_entry_lines(self, journal_entry):
        """Crear líneas del asiento contable"""
        # Línea de débito (Cuentas por cobrar)
        debit_line_vals = {
            'move_id': journal_entry.id,
            'name': _('Service Order: %s') % self.name,
            'account_id': self.partner_id.property_account_receivable_id.id,
            'partner_id': self.partner_id.id,
            'debit': self.total_amount,
            'credit': 0,
        }
        
        self.env['account.move.line'].create(debit_line_vals)
        
        # Línea de crédito (Ingresos por servicios)
        credit_line_vals = {
            'move_id': journal_entry.id,
            'name': _('Service Revenue: %s') % self.service_type_id.name,
            'account_id': self._get_service_account().id,
            'debit': 0,
            'credit': self.total_amount,
        }
        
        self.env['account.move.line'].create(credit_line_vals)
    
    def _get_service_journal(self):
        """Obtener diario para servicios"""
        service_journal = self.env['account.journal'].search([
            ('type', '=', 'sale'),
            ('company_id', '=', self.company_id.id)
        ], limit=1)
        
        if not service_journal:
            raise UserError(_('No sales journal found. Please configure accounting properly.'))
        
        return service_journal
    
    def action_view_invoice(self):
        """Ver factura asociada"""
        self.ensure_one()
        
        if not self.invoice_id:
            raise UserError(_('No invoice found for this service order.'))
        
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'account.move',
            'res_id': self.invoice_id.id,
            'view_mode': 'form',
            'target': 'current',
        }
    
    def action_view_journal_entry(self):
        """Ver asiento contable asociado"""
        self.ensure_one()
        
        if not self.journal_entry_id:
            raise UserError(_('No journal entry found for this service order.'))
        
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'account.move',
            'res_id': self.journal_entry_id.id,
            'view_mode': 'form',
            'target': 'current',
        }

class AccountMoveServiceOrder(models.Model):
    """
    Extensión del modelo de facturas para vincular con órdenes de servicio
    """
    _inherit = 'account.move'
    
    service_order_ids = fields.One2many(
        'inmoser.service.order',
        'invoice_id',
        string='Service Orders',
        help='Service orders related to this invoice'
    )
    
    service_order_count = fields.Integer(
        string='Service Orders Count',
        compute='_compute_service_order_count'
    )
    
    @api.depends('service_order_ids')
    def _compute_service_order_count(self):
        """Calcular número de órdenes de servicio"""
        for move in self:
            move.service_order_count = len(move.service_order_ids)
    
    def action_view_service_orders(self):
        """Ver órdenes de servicio relacionadas"""
        self.ensure_one()
        
        if not self.service_order_ids:
            raise UserError(_('No service orders found for this invoice.'))
        
        return {
            'type': 'ir.actions.act_window',
            'name': _('Service Orders'),
            'res_model': 'inmoser.service.order',
            'view_mode': 'tree,form',
            'domain': [('id', 'in', self.service_order_ids.ids)],
            'context': {'create': False},
        }

