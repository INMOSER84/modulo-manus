from odoo import fields, models

class FsmOrder(models.Model):
    _inherit = 'fsm.order'
    """
    Extensión del modelo `fsm.order` (Field Service Order) para integrar
    con las órdenes de servicio de Inmoser.
    Añade un campo para vincular una tarea de campo con una orden de servicio de Inmoser.
    """
    x_inmoser_service_order_id = fields.Many2one(
        'inmoser.service.order',
        string='Orden de Servicio Inmoser',
        help='Orden de Servicio de Inmoser relacionada a esta Tarea de Campo.'
    )
