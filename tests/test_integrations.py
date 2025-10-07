from odoo.tests import TransactionCase, tagged

@tagged('integrations')
class TestIntegrations(TransactionCase):
    
    def setUp(self):
        super(TestIntegrations, self).setUp()
        self.ServiceOrder = self.env['service.order']
        self.ServiceEquipment = self.env['service.equipment']
        self.SaleOrder = self.env['sale.order']
        self.AccountInvoice = self.env['account.move']
        
        # Crear datos de prueba
        self.equipment = self.ServiceEquipment.create({
            'name': 'Test Equipment',
            'serial_number': 'TEST123',
            'custom_stock': 10,
        })
        
        self.order = self.ServiceOrder.create({
            'client_id': self.env.ref('base.res_partner_1').id,
            'equipment_id': self.equipment.id,
            'service_type_id': self.env.ref('service_type_maintenance').id,
            'technician_id': self.env.ref('hr.employee_qdp').id,
            'scheduled_date': '2023-01-01 10:00:00',
            'is_sale_order': True,
        })
    
    def test_sale_order_integration(self):
        """Prueba de integración con órdenes de venta"""
        # Verificar que se crea una orden de venta
        self.assertTrue(self.order.sale_order_id, "No se creó la orden de venta")
        
        # Verificar relación entre orden de servicio y venta
        self.assertEqual(self.order.sale_order_id.origin, self.order.name)
        self.assertEqual(self.order.sale_order_id.partner_id, self.order.client_id)
    
    def test_invoice_integration(self):
        """Prueba de integración con facturación"""
        # Completar servicio
        self.order.action_confirm_service()
        self.order.action_start_service()
        self.order.action_complete_service()
        
        # Crear factura
        invoice = self.order.action_create_invoice()
        
        # Verificar que se crea una factura
        self.assertTrue(invoice, "No se creó la factura")
        self.assertEqual(invoice.partner_id, self.order.client_id)
        self.assertEqual(invoice.invoice_line_ids[0].price_unit, self.order.service_type_id.price)
    
    def test_stock_integration(self):
        """Prueba de integración con gestión de stock"""
        # Añadir parte al servicio
        self.env['service.order.refaction.line'].create({
            'order_id': self.order.id,
            'product_id': self.equipment.id,
            'quantity': 2,
            'price': 10.00,
        })
        
        # Guardar stock inicial
        initial_stock = self.equipment.custom_stock
        
        # Procesar servicio
        self.order.action_confirm_service()
        self.order.action_start_service()
        self.order.action_complete_service()
        
        # Verificar integración de stock
        self.assertEqual(self.equipment.custom_stock, initial_stock - 2)
        
        # Verificar historial de stock
        stock_history = self.env['stock.history'].search([('product_id', '=', self.equipment.id)])
        self.assertTrue(stock_history, "No se registró el historial de stock")
    
    def test_hr_integration(self):
        """Prueba de integración con recursos humanos"""
        # Verificar asignación de técnico
        self.assertTrue(self.order.technician_id, "No se asignó técnico")
        
        # Verificar que el técnico aparece en el historial de servicios del empleado
        services = self.env['service.order'].search([('technician_id', '=', self.order.technician_id.id)])
        self.assertIn(self.order, services, "El servicio no aparece en el historial del técnico")
