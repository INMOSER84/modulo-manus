from odoo.tests import TransactionCase, tagged
from odoo.exceptions import ValidationError

@tagged('service_equipment')
class TestServiceEquipment(TransactionCase):
    
    def setUp(self):
        super(TestServiceEquipment, self).setUp()
        self.ServiceEquipment = self.env['service.equipment']
        self.StockHistory = self.env['stock.history']
        
        # Crear datos de prueba
        self.equipment_data = {
            'name': 'Test Equipment',
            'serial_number': 'TEST123',
            'custom_stock': 10,
            'stock_alert_threshold': 5,
        }
    
    def test_create_equipment(self):
        """Prueba de creación de equipo de servicio"""
        equipment = self.ServiceEquipment.create(self.equipment_data)
        self.assertEqual(equipment.name, 'Test Equipment')
        self.assertEqual(equipment.custom_stock, 10)
        self.assertEqual(equipment.stock_alert_threshold, 5)
    
    def test_stock_validation(self):
        """Prueba de validación de stock"""
        with self.assertRaises(ValidationError):
            self.ServiceEquipment.create({
                'name': 'Invalid Equipment',
                'serial_number': 'INVALID',
                'custom_stock': -1,
            })
    
    def test_stock_history_creation(self):
        """Prueba de creación de historial de stock"""
        equipment = self.ServiceEquipment.create(self.equipment_data)
        
        # Modificar stock para crear historial
        equipment.write({'custom_stock': 8})
        
        # Verificar que se creó un registro de historial
        history = self.StockHistory.search([('product_id', '=', equipment.id)])
        self.assertTrue(history, "No se creó el historial de stock")
        self.assertEqual(history[0].new_stock, 8)
        self.assertEqual(history[0].previous_stock, 10)
    
    def test_update_inventory_action(self):
        """Prueba de acción de actualizar inventario"""
        equipment = self.ServiceEquipment.create(self.equipment_data)
        
        # Obtener acción de actualizar inventario
        action = equipment.action_update_inventory()
        
        self.assertEqual(action['type'], 'ir.actions.act_window')
        self.assertEqual(action['res_model'], 'stock.update.wizard')
        self.assertEqual(action['target'], 'new')
        self.assertEqual(action['context']['default_product_id'], equipment.id)
    
    def test_stock_alert_threshold(self):
        """Prueba de umbral de alerta de stock"""
        equipment = self.ServiceEquipment.create(self.equipment_data)
        
        # Establecer stock por debajo del umbral
        equipment.write({'custom_stock': 3})
        
        # Verificar que el stock está por debajo del umbral
        self.assertTrue(equipment.custom_stock <= equipment.stock_alert_threshold)
