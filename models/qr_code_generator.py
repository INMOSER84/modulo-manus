# -*- coding: utf-8 -*-

import qrcode
import base64
from io import BytesIO
from odoo import models, fields, api, _
from odoo.exceptions import UserError
import logging

_logger = logging.getLogger(__name__)

class QRCodeGenerator(models.Model):
    """
    Mixin para generar códigos QR
    """
    _name = 'inmoser.qr.generator'
    _description = 'QR Code Generator Mixin'
    
    def generate_qr_code(self, data, size=10, border=4):
        """
        Generar código QR a partir de datos
        
        Args:
            data (str): Datos a codificar en el QR
            size (int): Tamaño del QR (1-40)
            border (int): Borde del QR
            
        Returns:
            str: Imagen QR en base64
        """
        try:
            # Crear instancia QR
            qr = qrcode.QRCode(
                version=1,
                error_correction=qrcode.constants.ERROR_CORRECT_L,
                box_size=size,
                border=border,
            )
            
            # Añadir datos
            qr.add_data(data)
            qr.make(fit=True)
            
            # Crear imagen
            img = qr.make_image(fill_color="black", back_color="white")
            
            # Convertir a base64
            buffer = BytesIO()
            img.save(buffer, format='PNG')
            img_str = base64.b64encode(buffer.getvalue()).decode()
            
            return img_str
            
        except Exception as e:
            _logger.error(f"Error generating QR code: {str(e)}")
            raise UserError(_("Error generating QR code: %s") % str(e))
    
    def generate_equipment_qr_url(self, equipment_id):
        """
        Generar URL para acceso al portal del equipo
        
        Args:
            equipment_id (int): ID del equipo
            
        Returns:
            str: URL completa para el portal
        """
        base_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url')
        portal_url = f"{base_url}/inmoser/equipment/{equipment_id}"
        return portal_url
    
    def generate_service_order_qr_url(self, order_id):
        """
        Generar URL para acceso al portal de la orden de servicio
        
        Args:
            order_id (int): ID de la orden de servicio
            
        Returns:
            str: URL completa para el portal
        """
        base_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url')
        portal_url = f"{base_url}/inmoser/service-order/{order_id}"
        return portal_url

class ServiceEquipmentQR(models.Model):
    """
    Extensión del modelo de equipos con funcionalidad QR
    """
    _inherit = 'inmoser.service.equipment'
    
    def action_generate_qr_code(self):
        """Generar código QR para el equipo"""
        for record in self:
            try:
                # Generar URL del portal
                qr_generator = self.env['inmoser.qr.generator']
                portal_url = qr_generator.generate_equipment_qr_url(record.id)
                
                # Generar código QR
                qr_image = qr_generator.generate_qr_code(portal_url)
                
                # Actualizar campos
                record.qr_code = qr_image
                record.qr_code_text = portal_url
                
                # Mensaje de éxito
                record.message_post(
                    body=_('QR Code generated successfully. URL: %s') % portal_url,
                    message_type='notification'
                )
                
            except Exception as e:
                raise UserError(_("Error generating QR code: %s") % str(e))
    
    @api.model
    def create(self, vals):
        """Generar QR automáticamente al crear equipo"""
        record = super().create(vals)
        record.action_generate_qr_code()
        return record

class ServiceOrderQR(models.Model):
    """
    Extensión del modelo de órdenes de servicio con funcionalidad QR
    """
    _inherit = 'inmoser.service.order'
    
    qr_code_order = fields.Binary(
        string='Order QR Code',
        help='QR code for accessing this service order'
    )
    
    qr_code_order_text = fields.Char(
        string='Order QR Code URL',
        help='URL encoded in the QR code'
    )
    
    def action_generate_order_qr_code(self):
        """Generar código QR para la orden de servicio"""
        for record in self:
            try:
                # Generar URL del portal
                qr_generator = self.env['inmoser.qr.generator']
                portal_url = qr_generator.generate_service_order_qr_url(record.id)
                
                # Generar código QR
                qr_image = qr_generator.generate_qr_code(portal_url)
                
                # Actualizar campos
                record.qr_code_order = qr_image
                record.qr_code_order_text = portal_url
                
                # Mensaje de éxito
                record.message_post(
                    body=_('Order QR Code generated successfully. URL: %s') % portal_url,
                    message_type='notification'
                )
                
            except Exception as e:
                raise UserError(_("Error generating order QR code: %s") % str(e))
    
    @api.model
    def create(self, vals):
        """Generar QR automáticamente al crear orden"""
        record = super().create(vals)
        if record.state != 'draft':
            record.action_generate_order_qr_code()
        return record
    
    def write(self, vals):
        """Regenerar QR si cambia información relevante"""
        result = super().write(vals)
        
        # Regenerar QR si cambia el estado o información importante
        if any(field in vals for field in ['state', 'partner_id', 'equipment_id']):
            for record in self:
                if record.state != 'draft':
                    record.action_generate_order_qr_code()
        
        return result

