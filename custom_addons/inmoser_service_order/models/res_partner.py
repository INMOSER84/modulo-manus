from odoo import fields, models, api, _
class ResPartner(models.Model):
    _inherit = 'res.partner'
    """
    Extensión del modelo `res.partner` para añadir funcionalidades específicas
    de Inmoser para la gestión de clientes de servicio.
    Incluye campos para la secuencia de cliente, teléfono adicional,
    indicador de cliente de servicio, notas y equipos asociados.
    """
    # x_inmoser_client_sequence = fields.Char(string='Secuencia de Cliente', copy=False, readonly=True, index=True, default=lambda self: _('New'))
    x_inmoser_phone_mobile_2 = fields.Char(string='Teléfono Celular Adicional')
    # x_inmoser_is_service_client = fields.Boolean(string='Es Cliente de Servicios', default=False, help='Marca si el contacto es un cliente activo para órdenes de servicio.')
    # x_inmoser_client_notes = fields.Text(string='Notas del Cliente')
    # inmoser_equipment_ids = fields.One2many('inmoser.service.equipment', 'partner_id', string='Equipos de Servicio')
    @api.model_create_multi
    def create(self, vals_list):
        """
        Sobreescribe el método create para generar una secuencia de cliente
        si el partner es marcado como cliente de servicio y no tiene una secuencia.
        """
        for vals in vals_list:
            if vals.get('x_inmoser_is_service_client') and vals.get('x_inmoser_client_sequence', _('New')) == _('New'):
                vals['x_inmoser_client_sequence'] = self.env['ir.sequence'].next_by_code('inmoser.service.client') or _('New')
        return super().create(vals_list)
    def write(self, vals):
        """
        Sobreescribe el método write para generar una secuencia de cliente
        si el partner es marcado como cliente de servicio y no tiene una secuencia.
        """
        if vals.get('x_inmoser_is_service_client'):
            for partner in self.filtered(lambda p: p.x_inmoser_client_sequence == _('New')):
                partner.x_inmoser_client_sequence = self.env['ir.sequence'].next_by_code('inmoser.service.client') or _('New')
        return super().write(vals)
