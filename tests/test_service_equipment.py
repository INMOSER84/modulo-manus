# -*- coding: utf-8 -*-

from odoo.tests.common import TransactionCase
from odoo.exceptions import ValidationError
import logging

_logger = logging.getLogger(__name__)

class TestServiceEquipment(TransactionCase):
    """
    Tests unitarios para el modelo de equipos de servicio
    """
    
    def setUp(self):
        super().setUp()
        
        # Crear cliente de prueba
        self.partner = self.env['res.partner'].create({
            'name': 'Equipment Test Customer',
            'phone': '+1234567890',
            'email': 'equipment@test.com',
        })
    
    def test_equipment_creation(self):
        """Test creación básica de equipo"""
        equipment = self.env['inmoser.service.equipment'].create({
            'name': 'Test Equipment',
            'partner_id': self.partner.id,
            'equipment_type': 'computer',
            'brand': 'Test Brand',
            'model': 'Test Model',
            'serial_number': 'TEST123456',
            'location': 'Test Office',
        })
        
        # Verificar que se creó correctamente
        self.assertTrue(equipment.sequence)
        self.assertTrue(equipment.sequence.startswith('E'))
        self.assertEqual(equipment.partner_id, self.partner)
        self.assertEqual(equipment.equipment_type, 'computer')
        
    def test_equipment_sequence(self):
        """Test que la secuencia funciona correctamente"""
        equipment1 = self.env['inmoser.service.equipment'].create({
            'name': 'Test Equipment 1',
            'partner_id': self.partner.id,
            'equipment_type': 'computer',
        })
        
        equipment2 = self.env['inmoser.service.equipment'].create({
            'name': 'Test Equipment 2',
            'partner_id': self.partner.id,
            'equipment_type': 'printer',
        })
        
        # Verificar que las secuencias son diferentes
        self.assertNotEqual(equipment1.sequence, equipment2.sequence)
        self.assertTrue(equipment1.sequence.startswith('E'))
        self.assertTrue(equipment2.sequence.startswith('E'))
    
    def test_qr_code_generation(self):
        """Test generación de código QR para equipos"""
        equipment = self.env['inmoser.service.equipment'].create({
            'name': 'QR Test Equipment',
            'partner_id': self.partner.id,
            'equipment_type': 'computer',
        })
        
        # Generar QR
        equipment._generate_qr_code()
        
        self.assertTrue(equipment.qr_code)
        self.assertTrue(equipment.qr_url)
        self.assertIn(equipment.sequence, equipment.qr_url)
    
    def test_equipment_display_name(self):
        """Test nombre de visualización del equipo"""
        equipment = self.env['inmoser.service.equipment'].create({
            'name': 'Display Name Test',
            'partner_id': self.partner.id,
            'equipment_type': 'computer',
            'brand': 'TestBrand',
            'model': 'TestModel',
        })
        
        # El display_name debería incluir marca y modelo
        expected_name = f"Display Name Test (TestBrand TestModel)"
        self.assertEqual(equipment.display_name, expected_name)
    
    def test_equipment_service_count(self):
        """Test conteo de servicios del equipo"""
        equipment = self.env['inmoser.service.equipment'].create({
            'name': 'Service Count Test',
            'partner_id': self.partner.id,
            'equipment_type': 'computer',
        })
        
        # Crear tipo de servicio
        service_type = self.env['inmoser.service.type'].create({
            'name': 'Test Service Type',
            'base_price': 100.0,
        })
        
        # Crear órdenes de servicio
        for i in range(3):
            self.env['inmoser.service.order'].create({
                'partner_id': self.partner.id,
                'equipment_id': equipment.id,
                'service_type_id': service_type.id,
                'reported_fault': f'Test fault {i}',
            })
        
        # Verificar conteo
        self.assertEqual(equipment.service_order_count, 3)
    
    def test_equipment_warranty(self):
        """Test funcionalidad de garantía"""
        from datetime import date, timedelta
        
        equipment = self.env['inmoser.service.equipment'].create({
            'name': 'Warranty Test Equipment',
            'partner_id': self.partner.id,
            'equipment_type': 'computer',
            'warranty_expiry_date': date.today() + timedelta(days=30),
        })
        
        # Verificar que está en garantía
        self.assertTrue(equipment.is_under_warranty)
        
        # Cambiar fecha de garantía a pasado
        equipment.warranty_expiry_date = date.today() - timedelta(days=1)
        
        # Verificar que ya no está en garantía
        self.assertFalse(equipment.is_under_warranty)
    
    def test_equipment_validation(self):
        """Test validaciones del equipo"""
        # Test serial number único
        equipment1 = self.env['inmoser.service.equipment'].create({
            'name': 'Validation Test 1',
            'partner_id': self.partner.id,
            'equipment_type': 'computer',
            'serial_number': 'UNIQUE123',
        })
        
        # Intentar crear otro equipo con el mismo serial number
        with self.assertRaises(ValidationError):
            self.env['inmoser.service.equipment'].create({
                'name': 'Validation Test 2',
                'partner_id': self.partner.id,
                'equipment_type': 'computer',
                'serial_number': 'UNIQUE123',
            })
    
    def test_equipment_smart_buttons(self):
        """Test botones inteligentes del equipo"""
        equipment = self.env['inmoser.service.equipment'].create({
            'name': 'Smart Button Test',
            'partner_id': self.partner.id,
            'equipment_type': 'computer',
        })
        
        # Test botón de ver cliente
        action = equipment.action_view_customer()
        self.assertEqual(action['res_model'], 'res.partner')
        self.assertEqual(action['res_id'], self.partner.id)
        
        # Test botón de ver servicios
        action = equipment.action_view_service_orders()
        self.assertEqual(action['res_model'], 'inmoser.service.order')
        self.assertIn(('equipment_id', '=', equipment.id), action['domain'])
    
    def test_equipment_search(self):
        """Test funcionalidad de búsqueda"""
        equipment = self.env['inmoser.service.equipment'].create({
            'name': 'Search Test Equipment',
            'partner_id': self.partner.id,
            'equipment_type': 'computer',
            'brand': 'SearchBrand',
            'model': 'SearchModel',
            'serial_number': 'SEARCH123',
        })
        
        # Buscar por nombre
        found = self.env['inmoser.service.equipment'].search([
            ('name', 'ilike', 'Search Test')
        ])
        self.assertIn(equipment, found)
        
        # Buscar por marca
        found = self.env['inmoser.service.equipment'].search([
            ('brand', '=', 'SearchBrand')
        ])
        self.assertIn(equipment, found)
        
        # Buscar por serial number
        found = self.env['inmoser.service.equipment'].search([
            ('serial_number', '=', 'SEARCH123')
        ])
        self.assertIn(equipment, found)

class TestServiceType(TransactionCase):
    """
    Tests unitarios para tipos de servicio
    """
    
    def test_service_type_creation(self):
        """Test creación de tipo de servicio"""
        service_type = self.env['inmoser.service.type'].create({
            'name': 'Test Service Type',
            'description': 'Test description',
            'base_price': 150.0,
            'estimated_duration': 3.0,
            'requires_parts': True,
        })
        
        self.assertEqual(service_type.name, 'Test Service Type')
        self.assertEqual(service_type.base_price, 150.0)
        self.assertEqual(service_type.estimated_duration, 3.0)
        self.assertTrue(service_type.requires_parts)
    
    def test_service_type_validation(self):
        """Test validaciones de tipo de servicio"""
        # Precio no puede ser negativo
        with self.assertRaises(ValidationError):
            self.env['inmoser.service.type'].create({
                'name': 'Invalid Price Service',
                'base_price': -50.0,
            })
        
        # Duración no puede ser negativa
        with self.assertRaises(ValidationError):
            self.env['inmoser.service.type'].create({
                'name': 'Invalid Duration Service',
                'base_price': 100.0,
                'estimated_duration': -1.0,
            })
    
    def test_service_type_usage_count(self):
        """Test conteo de uso de tipos de servicio"""
        service_type = self.env['inmoser.service.type'].create({
            'name': 'Usage Count Test',
            'base_price': 100.0,
        })
        
        # Crear cliente y equipo
        partner = self.env['res.partner'].create({
            'name': 'Usage Test Customer',
        })
        
        equipment = self.env['inmoser.service.equipment'].create({
            'name': 'Usage Test Equipment',
            'partner_id': partner.id,
            'equipment_type': 'computer',
        })
        
        # Crear órdenes de servicio
        for i in range(2):
            self.env['inmoser.service.order'].create({
                'partner_id': partner.id,
                'equipment_id': equipment.id,
                'service_type_id': service_type.id,
                'reported_fault': f'Usage test fault {i}',
            })
        
        # Verificar conteo
        self.assertEqual(service_type.service_order_count, 2)

