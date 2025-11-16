from odoo import models, fields, api, _
from odoo.exceptions import UserError
import logging

_logger = logging.getLogger(__name__)

# Manejo seguro de dependencias externas
try:
    import qrcode
    import base64
    from io import BytesIO
    QR_CODE_AVAILABLE = True
except ImportError:
    _logger.warning("qrcode library not available. QR generation will fail.")
    QR_CODE_AVAILABLE = False

class InmoserServiceEquipment(models.Model):
    _name = 'inmoser.service.equipment'
    _description = 'Inmoser Service Equipment'
    _rec_name = 'name'

    name = fields.Char(
        string='Equipment Name/ID', 
        required=True
    )
    
    equipment_type = fields.Char(
        string='Equipment Type'
    )
    
    brand = fields.Char(
        string='Brand'
    )
    
    model = fields.Char(
        string='Model'
    )
    
    serial_number = fields.Char(
        string='Serial Number'
    )
    
    partner_id = fields.Many2one(
        'res.partner',
        string='Owner',
        help="The customer who owns this equipment."
    )
    
    notes = fields.Text(
        string='Notes'
    )
    
    purchase_date = fields.Date(
        string='Purchase Date'
    )
    
    warranty_end_date = fields.Date(
        string='Warranty End Date'
    )

    qr_code_text = fields.Char(
        string='QR Code Text',
        help='Text used to generate QR code',
        copy=False
    )
    
    qr_code = fields.Binary(
        string='QR Code Image',
        help='QR Code image generated from qr_code_text',
        attachment=True,
        copy=False
    )

    def action_generate_qr(self):
        """Generate QR code from qr_code_text field"""
        self.ensure_one()
        
        if not QR_CODE_AVAILABLE:
            raise UserError(_("QR Code library not installed. Please run: pip install qrcode[pil]"))
        
        if not self.qr_code_text:
            raise UserError(_('Please enter text for QR code generation'))
        
        try:
            # Generar QR code
            qr = qrcode.QRCode(
                version=1,
                error_correction=qrcode.constants.ERROR_CORRECT_L,
                box_size=10,
                border=4,
            )
            qr.add_data(self.qr_code_text)
            qr.make(fit=True)
            
            # Crear imagen PNG
            img = qr.make_image(fill_color="black", back_color="white")
            temp = BytesIO()
            img.save(temp, format='PNG')
            
            # Codificar a base64
            qr_image_base64 = base64.b64encode(temp.getvalue())
            
            # Guardar en el campo
            self.qr_code = qr_image_base64
            
        except Exception as e:
            _logger.error("Error generating QR code: %s", e)
            raise UserError(_("Error generating QR code: %s") % str(e))