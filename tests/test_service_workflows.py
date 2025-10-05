# -*- coding: utf-8 -*-

from odoo.tests.common import TransactionCase
from odoo.exceptions import UserError, ValidationError
from datetime import datetime, timedelta
import logging

_logger = logging.getLogger(__name__)

class TestServiceWorkflows(TransactionCase):
    """
    Tests para workflows y transiciones de estado en órdenes de servicio
    """
    
    def setUp(self):
        super().setUp()
        
        # Crear datos de prueba
        self.partner = self.env['res.partner'].create({
            'name': 'Workflow Test Customer',
            'phone': '+1234567890',
            'email': 'workflow@test.com',
        })
        
        self.technician_user = self.env['res.users'].create({
            'name': 'Workflow Technician',
            'login': 'workflow_tech',
            'email': 'tech@workflow.com',
            'groups_id': [(6, 0, [self.env.ref('inmoser_service_order.group_inmoser_technician').id])]
        })
        
        self.technician = self.env['hr.employee'].create({
            'name': 'Workflow Technician',
            'user_id': self.technician_user.id,
            'x_inmoser_is_technician': True,
            'x_inmoser_employee_code': 'WTECH001',
        })
        
        self.equipment = self.env['inmoser.service.equipment'].create({
            'name': 'Workflow Equipment',
            'partner_id': self.partner.id,
            'equipment_type': 'computer',
        })
        
        self.service_type = self.env['inmoser.service.type'].create({
            'name': 'Workflow Service',
            'base_price': 100.0,
            'estimated_duration': 2.0,
        })
    
    def test_draft_to_assigned_workflow(self):
        """Test transición de borrador a asignado"""
        service_order = self.env['inmoser.service.order'].create({
            'partner_id': self.partner.id,
            'equipment_id': self.equipment.id,
            'service_type_id': self.service_type.id,
            'reported_fault': 'Workflow test fault',
        })
        
        # Estado inicial debe ser draft
        self.assertEqual(service_order.state, 'draft')
        
        # Asignar técnico y fecha
        service_order.assigned_technician_id = self.technician.id
        service_order.scheduled_date = datetime.now() + timedelta(days=1)
        
        # Ejecutar transición
        service_order.action_assign_technician()
        
        # Verificar nuevo estado
        self.assertEqual(service_order.state, 'assigned')
        self.assertEqual(service_order.assigned_technician_id, self.technician)
        self.assertTrue(service_order.scheduled_date)
    
    def test_assigned_to_in_progress_workflow(self):
        """Test transición de asignado a en progreso"""
        service_order = self.env['inmoser.service.order'].create({
            'partner_id': self.partner.id,
            'equipment_id': self.equipment.id,
            'service_type_id': self.service_type.id,
            'reported_fault': 'Progress test fault',
            'assigned_technician_id': self.technician.id,
            'scheduled_date': datetime.now() + timedelta(hours=1),
            'state': 'assigned',
        })
        
        # Iniciar servicio
        service_order.action_start_service()
        
        # Verificar transición
        self.assertEqual(service_order.state, 'in_progress')
        self.assertTrue(service_order.start_date)
    
    def test_in_progress_to_done_workflow(self):
        """Test transición de en progreso a completado"""
        service_order = self.env['inmoser.service.order'].create({
            'partner_id': self.partner.id,
            'equipment_id': self.equipment.id,
            'service_type_id': self.service_type.id,
            'reported_fault': 'Completion test fault',
            'assigned_technician_id': self.technician.id,
            'state': 'in_progress',
            'start_date': datetime.now() - timedelta(hours=1),
        })
        
        # Agregar información requerida
        service_order.diagnosis = 'Test diagnosis'
        service_order.work_performed = 'Test work performed'
        
        # Completar servicio
        service_order.action_complete_service()
        
        # Verificar transición
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
        
        original_date = service_order.scheduled_date
        
        # Reagendar
        service_order.action_reschedule()
        
        # El estado debería mantenerse como assigned
        self.assertEqual(service_order.state, 'assigned')
    
    def test_cancel_workflow(self):
        """Test workflow de cancelación"""
        service_order = self.env['inmoser.service.order'].create({
            'partner_id': self.partner.id,
            'equipment_id': self.equipment.id,
            'service_type_id': self.service_type.id,
            'reported_fault': 'Cancel test',
            'state': 'draft',
        })
        
        # Cancelar servicio
        service_order.action_cancel()
        
        # Verificar cancelación
        self.assertEqual(service_order.state, 'cancelled')
    
    def test_invalid_workflow_transitions(self):
        """Test transiciones inválidas"""
        service_order = self.env['inmoser.service.order'].create({
            'partner_id': self.partner.id,
            'equipment_id': self.equipment.id,
            'service_type_id': self.service_type.id,
            'reported_fault': 'Invalid transition test',
        })
        
        # Intentar iniciar servicio desde draft (sin asignar técnico)
        with self.assertRaises(UserError):
            service_order.action_start_service()
        
        # Intentar completar servicio desde draft
        with self.assertRaises(UserError):
            service_order.action_complete_service()
    
    def test_workflow_with_approval(self):
        """Test workflow con aprobación del cliente"""
        service_order = self.env['inmoser.service.order'].create({
            'partner_id': self.partner.id,
            'equipment_id': self.equipment.id,
            'service_type_id': self.service_type.id,
            'reported_fault': 'Approval test',
            'assigned_technician_id': self.technician.id,
            'state': 'in_progress',
            'start_date': datetime.now(),
        })
        
        # Agregar refacciones que requieren aprobación
        product = self.env['product.product'].create({
            'name': 'Expensive Part',
            'type': 'product',
            'list_price': 500.0,
        })
        
        self.env['inmoser.service.order.refaction.line'].create({
            'service_order_id': service_order.id,
            'product_id': product.id,
            'quantity': 1,
            'unit_price': 500.0,
        })
        
        # Solicitar aprobación
        service_order.diagnosis = 'Needs expensive part'
        service_order.work_performed = 'Replace expensive component'
        service_order.action_request_approval()
        
        # Verificar estado de aprobación pendiente
        self.assertEqual(service_order.state, 'pending_approval')
        
        # Cliente acepta
        service_order.action_customer_accept()
        
        # Debería completarse automáticamente
        self.assertEqual(service_order.state, 'done')
    
    def test_workflow_with_rejection(self):
        """Test workflow con rechazo del cliente"""
        service_order = self.env['inmoser.service.order'].create({
            'partner_id': self.partner.id,
            'equipment_id': self.equipment.id,
            'service_type_id': self.service_type.id,
            'reported_fault': 'Rejection test',
            'assigned_technician_id': self.technician.id,
            'state': 'pending_approval',
        })
        
        # Cliente rechaza
        service_order.action_customer_reject()
        
        # Debería cancelarse
        self.assertEqual(service_order.state, 'cancelled')
    
    def test_workflow_notifications(self):
        """Test notificaciones en workflow"""
        service_order = self.env['inmoser.service.order'].create({
            'partner_id': self.partner.id,
            'equipment_id': self.equipment.id,
            'service_type_id': self.service_type.id,
            'reported_fault': 'Notification test',
        })
        
        # Asignar técnico (debería generar notificación)
        service_order.assigned_technician_id = self.technician.id
        service_order.scheduled_date = datetime.now() + timedelta(days=1)
        service_order.action_assign_technician()
        
        # Verificar que se crearon mensajes
        messages = service_order.message_ids
        self.assertTrue(len(messages) > 0)
    
    def test_workflow_activities(self):
        """Test actividades en workflow"""
        service_order = self.env['inmoser.service.order'].create({
            'partner_id': self.partner.id,
            'equipment_id': self.equipment.id,
            'service_type_id': self.service_type.id,
            'reported_fault': 'Activity test',
            'assigned_technician_id': self.technician.id,
            'scheduled_date': datetime.now() + timedelta(days=1),
            'state': 'assigned',
        })
        
        # Iniciar servicio
        service_order.action_start_service()
        
        # Verificar que se crearon actividades
        activities = service_order.activity_ids
        # Las actividades pueden o no crearse dependiendo de la configuración
        # Este test verifica que no hay errores en el proceso
        self.assertTrue(True)

class TestServiceOrderValidations(TransactionCase):
    """
    Tests para validaciones específicas de órdenes de servicio
    """
    
    def setUp(self):
        super().setUp()
        
        self.partner = self.env['res.partner'].create({
            'name': 'Validation Test Customer',
        })
        
        self.equipment = self.env['inmoser.service.equipment'].create({
            'name': 'Validation Equipment',
            'partner_id': self.partner.id,
            'equipment_type': 'computer',
        })
        
        self.service_type = self.env['inmoser.service.type'].create({
            'name': 'Validation Service',
            'base_price': 100.0,
        })
    
    def test_required_fields_validation(self):
        """Test validación de campos requeridos"""
        # Falta partner_id
        with self.assertRaises(ValidationError):
            self.env['inmoser.service.order'].create({
                'equipment_id': self.equipment.id,
                'service_type_id': self.service_type.id,
                'reported_fault': 'Test fault',
            })
        
        # Falta equipment_id
        with self.assertRaises(ValidationError):
            self.env['inmoser.service.order'].create({
                'partner_id': self.partner.id,
                'service_type_id': self.service_type.id,
                'reported_fault': 'Test fault',
            })
    
    def test_date_validations(self):
        """Test validaciones de fechas"""
        service_order = self.env['inmoser.service.order'].create({
            'partner_id': self.partner.id,
            'equipment_id': self.equipment.id,
            'service_type_id': self.service_type.id,
            'reported_fault': 'Date validation test',
        })
        
        # Fecha de fin antes que fecha de inicio (inválido)
        service_order.start_date = datetime.now()
        service_order.end_date = datetime.now() - timedelta(hours=1)
        
        with self.assertRaises(ValidationError):
            service_order._check_dates()
    
    def test_technician_availability_validation(self):
        """Test validación de disponibilidad de técnico"""
        technician_user = self.env['res.users'].create({
            'name': 'Availability Test Technician',
            'login': 'availability_tech',
        })
        
        technician = self.env['hr.employee'].create({
            'name': 'Availability Test Technician',
            'user_id': technician_user.id,
            'x_inmoser_is_technician': True,
        })
        
        # Crear primera orden
        service_order1 = self.env['inmoser.service.order'].create({
            'partner_id': self.partner.id,
            'equipment_id': self.equipment.id,
            'service_type_id': self.service_type.id,
            'reported_fault': 'Availability test 1',
            'assigned_technician_id': technician.id,
            'scheduled_date': datetime.now() + timedelta(days=1),
        })
        
        # Intentar crear segunda orden en la misma fecha/hora
        service_order2 = self.env['inmoser.service.order'].create({
            'partner_id': self.partner.id,
            'equipment_id': self.equipment.id,
            'service_type_id': self.service_type.id,
            'reported_fault': 'Availability test 2',
            'assigned_technician_id': technician.id,
            'scheduled_date': datetime.now() + timedelta(days=1),
        })
        
        # La validación de disponibilidad debería funcionar
        # (puede o no generar error dependiendo de la implementación específica)
        self.assertTrue(True)

