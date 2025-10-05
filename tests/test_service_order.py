# -*- coding: utf-8 -*-

from odoo.tests.common import TransactionCase
from odoo.exceptions import UserError, ValidationError
from datetime import datetime, timedelta
import logging

_logger = logging.getLogger(__name__)

class TestServiceOrder(TransactionCase):
    """
    Tests unitarios para el modelo de órdenes de servicio
    """
    
    def setUp(self):
        super().setUp()
        
        # Crear datos de prueba
        self.partner = self.env['res.partner'].create({
            'name': 'Test Customer',
            'phone': '+1234567890',
            'email': 'test@customer.com',
            'street': '123 Test Street',
            'city': 'Test City',
        })
        
        self.technician_user = self.env['res.users'].create({
            'name': 'Test Technician',
            'login': 'test_technician',
            'email': 'technician@test.com',
            'groups_id': [(6, 0, [self.env.ref('inmoser_service_order.group_inmoser_technician').id])]
        })
        
        self.technician = self.env['hr.employee'].create({
            'name': 'Test Technician',
            'user_id': self.technician_user.id,
            'x_inmoser_is_technician': True,
            'x_inmoser_employee_code': 'TECH001',
            'x_inmoser_specialization': 'electronics',
        })
        
        self.equipment = self.env['inmoser.service.equipment'].create({
            'name': 'Test Equipment',
            'partner_id': self.partner.id,
            'equipment_type': 'computer',
            'brand': 'Test Brand',
            'model': 'Test Model',
            'serial_number': 'TEST123456',
            'location': 'Office',
        })
        
        self.service_type = self.env['inmoser.service.type'].create({
            'name': 'Test Service',
            'description': 'Test service type',
            'base_price': 100.0,
            'estimated_duration': 2.0,
        })
    
    def test_service_order_creation(self):
        """Test creación básica de orden de servicio"""
        service_order = self.env['inmoser.service.order'].create({
            'partner_id': self.partner.id,
            'equipment_id': self.equipment.id,
            'service_type_id': self.service_type.id,
            'reported_fault': 'Test fault description',
            'priority': 'normal',
        })
        
        # Verificar que se creó correctamente
        self.assertTrue(service_order.name)
        self.assertTrue(service_order.name.startswith('OS'))
        self.assertEqual(service_order.state, 'draft')
        self.assertEqual(service_order.partner_id, self.partner)
        self.assertEqual(service_order.equipment_id, self.equipment)
        
    def test_service_order_sequence(self):
        """Test que la secuencia funciona correctamente"""
        order1 = self.env['inmoser.service.order'].create({
            'partner_id': self.partner.id,
            'equipment_id': self.equipment.id,
            'service_type_id': self.service_type.id,
            'reported_fault': 'Test fault 1',
        })
        
        order2 = self.env['inmoser.service.order'].create({
            'partner_id': self.partner.id,
            'equipment_id': self.equipment.id,
            'service_type_id': self.service_type.id,
            'reported_fault': 'Test fault 2',
        })
        
        # Verificar que las secuencias son diferentes
        self.assertNotEqual(order1.name, order2.name)
        self.assertTrue(order1.name.startswith('OS'))
        self.assertTrue(order2.name.startswith('OS'))
    
    def test_assign_technician(self):
        """Test asignación de técnico"""
        service_order = self.env['inmoser.service.order'].create({
            'partner_id': self.partner.id,
            'equipment_id': self.equipment.id,
            'service_type_id': self.service_type.id,
            'reported_fault': 'Test fault',
        })
        
        # Asignar técnico
        service_order.assigned_technician_id = self.technician.id
        service_order.scheduled_date = datetime.now() + timedelta(days=1)
        
        # Cambiar estado a asignado
        service_order.action_assign_technician()
        
        self.assertEqual(service_order.state, 'assigned')
        self.assertEqual(service_order.assigned_technician_id, self.technician)
        
    def test_start_service(self):
        """Test inicio de servicio"""
        service_order = self.env['inmoser.service.order'].create({
            'partner_id': self.partner.id,
            'equipment_id': self.equipment.id,
            'service_type_id': self.service_type.id,
            'reported_fault': 'Test fault',
            'assigned_technician_id': self.technician.id,
            'scheduled_date': datetime.now() + timedelta(hours=1),
            'state': 'assigned',
        })
        
        # Iniciar servicio
        service_order.action_start_service()
        
        self.assertEqual(service_order.state, 'in_progress')
        self.assertTrue(service_order.start_date)
        
    def test_complete_service(self):
        """Test completar servicio"""
        service_order = self.env['inmoser.service.order'].create({
            'partner_id': self.partner.id,
            'equipment_id': self.equipment.id,
            'service_type_id': self.service_type.id,
            'reported_fault': 'Test fault',
            'assigned_technician_id': self.technician.id,
            'state': 'in_progress',
            'start_date': datetime.now(),
            'diagnosis': 'Test diagnosis',
            'work_performed': 'Test work performed',
        })
        
        # Completar servicio
        service_order.action_complete_service()
        
        self.assertEqual(service_order.state, 'done')
        self.assertTrue(service_order.end_date)
        
    def test_cancel_service(self):
        """Test cancelar servicio"""
        service_order = self.env['inmoser.service.order'].create({
            'partner_id': self.partner.id,
            'equipment_id': self.equipment.id,
            'service_type_id': self.service_type.id,
            'reported_fault': 'Test fault',
            'state': 'draft',
        })
        
        # Cancelar servicio
        service_order.action_cancel()
        
        self.assertEqual(service_order.state, 'cancelled')
        
    def test_validation_errors(self):
        """Test validaciones y errores"""
        service_order = self.env['inmoser.service.order'].create({
            'partner_id': self.partner.id,
            'equipment_id': self.equipment.id,
            'service_type_id': self.service_type.id,
            'reported_fault': 'Test fault',
        })
        
        # Intentar iniciar servicio sin asignar técnico
        with self.assertRaises(UserError):
            service_order.action_start_service()
            
        # Intentar completar servicio sin estar en progreso
        with self.assertRaises(UserError):
            service_order.action_complete_service()
    
    def test_refaction_lines(self):
        """Test líneas de refacciones"""
        product = self.env['product.product'].create({
            'name': 'Test Part',
            'type': 'product',
            'list_price': 50.0,
        })
        
        service_order = self.env['inmoser.service.order'].create({
            'partner_id': self.partner.id,
            'equipment_id': self.equipment.id,
            'service_type_id': self.service_type.id,
            'reported_fault': 'Test fault',
        })
        
        # Crear línea de refacción
        refaction_line = self.env['inmoser.service.order.refaction.line'].create({
            'service_order_id': service_order.id,
            'product_id': product.id,
            'description': 'Test part used',
            'quantity': 2,
            'unit_price': 50.0,
        })
        
        self.assertEqual(refaction_line.total_price, 100.0)
        self.assertEqual(service_order.total_amount, 100.0)
    
    def test_qr_code_generation(self):
        """Test generación de código QR"""
        service_order = self.env['inmoser.service.order'].create({
            'partner_id': self.partner.id,
            'equipment_id': self.equipment.id,
            'service_type_id': self.service_type.id,
            'reported_fault': 'Test fault',
        })
        
        # Generar QR
        service_order._generate_qr_code()
        
        self.assertTrue(service_order.qr_code)
        self.assertTrue(service_order.qr_url)
        
    def test_duration_calculation(self):
        """Test cálculo de duración"""
        service_order = self.env['inmoser.service.order'].create({
            'partner_id': self.partner.id,
            'equipment_id': self.equipment.id,
            'service_type_id': self.service_type.id,
            'reported_fault': 'Test fault',
            'start_date': datetime(2024, 1, 1, 10, 0, 0),
            'end_date': datetime(2024, 1, 1, 12, 30, 0),
        })
        
        # Verificar cálculo de duración
        self.assertEqual(service_order.duration, 2.5)
    
    def test_smart_buttons(self):
        """Test botones inteligentes"""
        service_order = self.env['inmoser.service.order'].create({
            'partner_id': self.partner.id,
            'equipment_id': self.equipment.id,
            'service_type_id': self.service_type.id,
            'reported_fault': 'Test fault',
        })
        
        # Test botón de ver cliente
        action = service_order.action_view_customer()
        self.assertEqual(action['res_model'], 'res.partner')
        self.assertEqual(action['res_id'], self.partner.id)
        
        # Test botón de ver equipo
        action = service_order.action_view_equipment()
        self.assertEqual(action['res_model'], 'inmoser.service.equipment')
        self.assertEqual(action['res_id'], self.equipment.id)

class TestServiceOrderWorkflows(TransactionCase):
    """
    Tests para workflows y transiciones de estado
    """
    
    def setUp(self):
        super().setUp()
        
        # Crear datos de prueba básicos
        self.partner = self.env['res.partner'].create({
            'name': 'Workflow Test Customer',
            'phone': '+1234567890',
        })
        
        self.technician_user = self.env['res.users'].create({
            'name': 'Workflow Test Technician',
            'login': 'workflow_technician',
            'email': 'workflow@test.com',
        })
        
        self.technician = self.env['hr.employee'].create({
            'name': 'Workflow Test Technician',
            'user_id': self.technician_user.id,
            'x_inmoser_is_technician': True,
        })
        
        self.equipment = self.env['inmoser.service.equipment'].create({
            'name': 'Workflow Test Equipment',
            'partner_id': self.partner.id,
            'equipment_type': 'computer',
        })
        
        self.service_type = self.env['inmoser.service.type'].create({
            'name': 'Workflow Test Service',
            'base_price': 100.0,
        })
    
    def test_complete_workflow(self):
        """Test workflow completo de orden de servicio"""
        # 1. Crear orden
        service_order = self.env['inmoser.service.order'].create({
            'partner_id': self.partner.id,
            'equipment_id': self.equipment.id,
            'service_type_id': self.service_type.id,
            'reported_fault': 'Workflow test fault',
        })
        
        self.assertEqual(service_order.state, 'draft')
        
        # 2. Asignar técnico
        service_order.assigned_technician_id = self.technician.id
        service_order.scheduled_date = datetime.now() + timedelta(days=1)
        service_order.action_assign_technician()
        
        self.assertEqual(service_order.state, 'assigned')
        
        # 3. Iniciar servicio
        service_order.action_start_service()
        
        self.assertEqual(service_order.state, 'in_progress')
        self.assertTrue(service_order.start_date)
        
        # 4. Agregar diagnóstico y trabajo
        service_order.diagnosis = 'Test diagnosis'
        service_order.work_performed = 'Test work performed'
        
        # 5. Completar servicio
        service_order.action_complete_service()
        
        self.assertEqual(service_order.state, 'done')
        self.assertTrue(service_order.end_date)
        self.assertTrue(service_order.duration > 0)
    
    def test_reschedule_workflow(self):
        """Test workflow de reagendamiento"""
        service_order = self.env['inmoser.service.order'].create({
            'partner_id': self.partner.id,
            'equipment_id': self.equipment.id,
            'service_type_id': self.service_type.id,
            'reported_fault': 'Reschedule test',
            'assigned_technician_id': self.technician.id,
            'scheduled_date': datetime.now() + timedelta(days=1),
            'state': 'assigned',
        })
        
        # Reagendar
        new_date = datetime.now() + timedelta(days=2)
        service_order.action_reschedule()
        
        # Verificar que se puede reagendar
        self.assertTrue(True)  # Si llega aquí, no hubo errores
    
    def test_invalid_transitions(self):
        """Test transiciones inválidas de estado"""
        service_order = self.env['inmoser.service.order'].create({
            'partner_id': self.partner.id,
            'equipment_id': self.equipment.id,
            'service_type_id': self.service_type.id,
            'reported_fault': 'Invalid transition test',
        })
        
        # Intentar completar desde draft (inválido)
        with self.assertRaises(UserError):
            service_order.action_complete_service()
        
        # Intentar iniciar sin técnico asignado (inválido)
        with self.assertRaises(UserError):
            service_order.action_start_service()

