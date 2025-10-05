from odoo.tests import TransactionCase, tagged
from odoo.exceptions import ValidationError

@tagged('service_order')
class TestServiceOrder(TransactionCase):
    
    def setUp(self):
        super(TestServiceOrder, self).setUp()
        self.ServiceOrder = self.env['service.order']
        self.ServiceEquipment = self.env['service.equipment']
        self.ServiceType = self.env['service.type']
        
        # Crear datos de prueba
        self.equipment = self.ServiceEquipment.create({
            'name': 'Test Equipment',
            'serial_number': 'TEST123',
            'custom_stock': 10,
        })
        
        self.service_type = self.ServiceType.create({
            'name': 'Test Service',
            'code': 'TS',
            'price': 100.00,
        })
        
        self.order_data = {
            'client_id': self.env.ref('base.res_partner_1').id,
            'equipment_id': self.equipment.id,
            'service_type_id': self.service_type.id,
            'technician_id': self.env.ref('hr.employee_qdp').id,
            'scheduled_date': '2023-01-01 10:00:00',
            'custom_sale_type': 'service',
            'priority': '0',
        }
    
    def test_create_service_order(self):
        """Prueba de creación de orden de servicio"""
        order = self.ServiceOrder.create(self.order_data)
        self.assertEqual(order.state, 'draft')
        self.assertEqual(order.custom_sale_type, 'service')
        self.assertEqual(order.priority, '0')
    
    def test_confirm_service_order(self):
        """Prueba de confirmación de orden de servicio"""
        order = self.ServiceOrder.create(self.order_data)
        order.action_confirm_service()
        self.assertEqual(order.state, 'confirmed')
    
    def test_stock_validation_on_confirm(self):
        """Prueba de validación de stock al confirmar"""
        # Crear orden con partes que exceden el stock
        order = self.ServiceOrder.create(self.order_data)
        
        # Añadir parte que excede el stock disponible
        self.env['service.order.refaction.line'].create({
            'order_id': order.id,
            'product_id': self.equipment.id,
            'quantity': 15,  # Más de las 10 disponibles
            'price': 10.00,
        })
        
        with self.assertRaises(ValidationError):
            order.action_confirm_service()
    
    def test_cancel_service_order(self):
        """Prueba de cancelación de orden de servicio"""
        order = self.ServiceOrder.create(self.order_data)
        order.action_confirm_service()
        order.action_cancel_service()
        self.assertEqual(order.state, 'cancel')
    
    def test_sale_order_creation(self):
        """Prueba de creación de orden de venta asociada"""
        order = self.ServiceOrder.create(self.order_data)
        order.write({'is_sale_order': True})
        
        # Verificar que se crea una orden de venta
        self.assertTrue(order.sale_order_id, "No se creó la orden de venta")
        self.assertEqual(order.sale_order_id.partner_id, order.client_id)
        self.assertEqual(order.sale_order_id.custom_sale_type, order.custom_sale_type)
