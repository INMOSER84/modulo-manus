from odoo.tests import TransactionCase, tagged

@tagged('service_workflows')
class TestServiceWorkflows(TransactionCase):
    
    def setUp(self):
        super(TestServiceWorkflows, self).setUp()
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
        
        self.order = self.ServiceOrder.create({
            'client_id': self.env.ref('base.res_partner_1').id,
            'equipment_id': self.equipment.id,
            'service_type_id': self.service_type.id,
            'technician_id': self.env.ref('hr.employee_qdp').id,
            'scheduled_date': '2023-01-01 10:00:00',
        })
    
    def test_complete_workflow(self):
        """Prueba del flujo de trabajo completo"""
        # Estado inicial: draft
        self.assertEqual(self.order.state, 'draft')
        
        # Confirmar orden
        self.order.action_confirm_service()
        self.assertEqual(self.order.state, 'confirmed')
        
        # Iniciar servicio
        self.order.action_start_service()
        self.assertEqual(self.order.state, 'in_progress')
        
        # Completar servicio
        self.order.action_complete_service()
        self.assertEqual(self.order.state, 'done')
    
    def test_cancel_workflow(self):
        """Prueba de cancelación en diferentes estados"""
        # Confirmar orden
        self.order.action_confirm_service()
        self.assertEqual(self.order.state, 'confirmed')
        
        # Cancelar orden
        self.order.action_cancel_service()
        self.assertEqual(self.order.state, 'cancel')
    
    def test_stock_deduction_on_complete(self):
        """Prueba de deducción de stock al completar servicio"""
        # Añadir parte al servicio
        self.env['service.order.refaction.line'].create({
            'order_id': self.order.id,
            'product_id': self.equipment.id,
            'quantity': 2,
            'price': 10.00,
        })
        
        # Guardar stock inicial
        initial_stock = self.equipment.custom_stock
        
        # Completar servicio
        self.order.action_confirm_service()
        self.order.action_start_service()
        self.order.action_complete_service()
        
        # Verificar que el stock se redujo
        self.assertEqual(self.equipment.custom_stock, initial_stock - 2)
    
    def test_stock_restoration_on_cancel(self):
        """Prueba de restauración de stock al cancelar"""
        # Añadir parte al servicio
        self.env['service.order.refaction.line'].create({
            'order_id': self.order.id,
            'product_id': self.equipment.id,
            'quantity': 2,
            'price': 10.00,
        })
        
        # Guardar stock inicial
        initial_stock = self.equipment.custom_stock
        
        # Confirmar y cancelar servicio
        self.order.action_confirm_service()
        self.order.action_cancel_service()
        
        # Verificar que el stock se restauró
        self.assertEqual(self.equipment.custom_stock, initial_stock)
