from odoo import fields, models
class AccountMove(models.Model):
    _inherit = 'account.move'
    """
    Extensión del modelo `account.move` para vincular facturas
    con órdenes de servicio de Inmoser.
    """
    service_order_id = fields.Many2one('inmoser.service.order', string='Orden de Servicio', readonly=True, copy=False, help='Orden de servicio que generó esta factura.')
