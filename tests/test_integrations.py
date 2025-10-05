# -*- coding: utf-8 -*-

from odoo.tests.common import TransactionCase
from odoo.exceptions import UserError
from datetime import datetime, timedelta
import logging

_logger = logging.getLogger(__name__)

class TestAccountingIntegration(TransactionCase):
    """
    Tests para integración con módulo de contabilidad
    """
    
    def setUp(self):
        super().setUp()
        
        # Crear datos de prueba
        self.partner = self.env['res.partner'].create({
            'name': 'Accounting Test Customer',
            'email': 'accounting@test.com',
            'is_company': True,
        })
        
        self.equipment = self.env['inmoser.service.equipment'].create({
            'name': 'Accounting Test Equipment',
            'partner_id': self.partner.id,
            'equipment_type': 'computer',
        })
        
        self.service_type = self.env['inmoser.service.type'].create({
            'name': 'Accounting Test Service',
            'base_price': 200.0,
        })
        
        self.product = self.env['product.product'].create({
            'name': 'Test Part',
            'type': 'product',
            'list_price': 50.0,
        })
    
    def test_invoice_creation(self):
        """Test creación de factura desde orden de servicio"""
        service_order = self.env['inmoser.service.order'].create({
            'partner_id': self.partner.id,
            'equipment_id': self.equipment.id,
            'service_type_id': self.service_type.id,
            'reported_fault': 'Invoice test',
            'state': 'done',
            'diagnosis': 'Test diagnosis',
            'work_performed': 'Test work',
        })
        
        # Agregar refacción
        self.env['inmoser.service.order.refaction.line'].create({
            'service_order_id': service_order.id,
            'product_id': self.product.id,
            'quantity': 2,
            'unit_price': 50.0,
        })
        
        # Crear factura
        action = service_order.action_create_invoice()
        
        # Verificar que se creó la factura
        self.assertTrue(service_order.invoice_id)
        self.assertEqual(service_order.invoice_status, 'invoiced')
        
        # Verificar líneas de factura
        invoice = service_order.invoice_id
        self.assertTrue(len(invoice.invoice_line_ids) >= 2)  # Servicio + refacción
    
    def test_journal_entry_creation(self):
        """Test creación de asiento contable"""
        service_order = self.env['inmoser.service.order'].create({
            'partner_id': self.partner.id,
            'equipment_id': self.equipment.id,
            'service_type_id': self.service_type.id,
            'reported_fault': 'Journal entry test',
            'state': 'done',
            'total_amount': 250.0,
        })
        
        # Crear asiento contable
        action = service_order.action_create_journal_entry()
        
        # Verificar que se creó el asiento
        self.assertTrue(service_order.journal_entry_id)
        
        # Verificar líneas del asiento
        journal_entry = service_order.journal_entry_id
        self.assertEqual(len(journal_entry.line_ids), 2)  # Débito y crédito
        
        # Verificar que está confirmado
        self.assertEqual(journal_entry.state, 'posted')
    
    def test_invoice_validation(self):
        """Test validaciones de facturación"""
        service_order = self.env['inmoser.service.order'].create({
            'partner_id': self.partner.id,
            'equipment_id': self.equipment.id,
            'service_type_id': self.service_type.id,
            'reported_fault': 'Invoice validation test',
            'state': 'draft',  # No completado
        })
        
        # Intentar crear factura de orden no completada
        with self.assertRaises(UserError):
            service_order.action_create_invoice()
    
    def test_payment_status_computation(self):
        """Test cálculo de estado de pago"""
        service_order = self.env['inmoser.service.order'].create({
            'partner_id': self.partner.id,
            'equipment_id': self.equipment.id,
            'service_type_id': self.service_type.id,
            'reported_fault': 'Payment status test',
            'state': 'done',
        })
        
        # Sin factura
        self.assertEqual(service_order.payment_status, 'not_paid')
        
        # Con factura
        service_order.action_create_invoice()
        # El estado dependerá del estado de pago de la factura
        self.assertIn(service_order.payment_status, ['not_paid', 'partial', 'paid'])

class TestStockIntegration(TransactionCase):
    """
    Tests para integración con módulo de inventario
    """
    
    def setUp(self):
        super().setUp()
        
        self.partner = self.env['res.partner'].create({
            'name': 'Stock Test Customer',
        })
        
        self.equipment = self.env['inmoser.service.equipment'].create({
            'name': 'Stock Test Equipment',
            'partner_id': self.partner.id,
            'equipment_type': 'computer',
        })
        
        self.service_type = self.env['inmoser.service.type'].create({
            'name': 'Stock Test Service',
            'base_price': 100.0,
        })
        
        self.product = self.env['product.product'].create({
            'name': 'Stock Test Part',
            'type': 'product',
            'list_price': 25.0,
        })
        
        # Crear stock inicial
        self.env['stock.quant']._update_available_quantity(
            self.product,
            self.env.ref('stock.stock_location_stock'),
            10.0
        )
    
    def test_delivery_creation(self):
        """Test creación de entrega para refacciones"""
        service_order = self.env['inmoser.service.order'].create({
            'partner_id': self.partner.id,
            'equipment_id': self.equipment.id,
            'service_type_id': self.service_type.id,
            'reported_fault': 'Delivery test',
            'state': 'done',
        })
        
        # Agregar refacción
        self.env['inmoser.service.order.refaction.line'].create({
            'service_order_id': service_order.id,
            'product_id': self.product.id,
            'quantity': 2,
            'unit_price': 25.0,
        })
        
        # Crear entrega
        action = service_order.action_create_delivery()
        
        # Verificar que se creó el picking
        self.assertTrue(len(service_order.picking_ids) > 0)
        self.assertEqual(service_order.delivery_status, 'pending')
    
    def test_stock_availability_check(self):
        """Test verificación de disponibilidad de stock"""
        service_order = self.env['inmoser.service.order'].create({
            'partner_id': self.partner.id,
            'equipment_id': self.equipment.id,
            'service_type_id': self.service_type.id,
            'reported_fault': 'Stock availability test',
        })
        
        # Agregar refacción con cantidad disponible
        self.env['inmoser.service.order.refaction.line'].create({
            'service_order_id': service_order.id,
            'product_id': self.product.id,
            'quantity': 5,  # Hay 10 disponibles
            'unit_price': 25.0,
        })
        
        # Verificar disponibilidad
        action = service_order.action_check_stock_availability()
        
        # Debería indicar que hay stock disponible
        self.assertEqual(action['params']['type'], 'success')
    
    def test_product_service_categorization(self):
        """Test categorización de productos para servicios"""
        # Marcar producto como parte de servicio
        self.product.is_service_part = True
        self.product.service_category = 'electronic'
        self.product.min_stock_service = 5.0
        
        self.assertTrue(self.product.is_service_part)
        self.assertEqual(self.product.service_category, 'electronic')
        
        # Crear orden que use este producto
        service_order = self.env['inmoser.service.order'].create({
            'partner_id': self.partner.id,
            'equipment_id': self.equipment.id,
            'service_type_id': self.service_type.id,
            'reported_fault': 'Product categorization test',
        })
        
        self.env['inmoser.service.order.refaction.line'].create({
            'service_order_id': service_order.id,
            'product_id': self.product.id,
            'quantity': 1,
            'unit_price': 25.0,
        })
        
        # Verificar conteo de uso
        self.assertTrue(self.product.service_order_count > 0)

class TestHRIntegration(TransactionCase):
    """
    Tests para integración con módulo de recursos humanos
    """
    
    def setUp(self):
        super().setUp()
        
        self.technician_user = self.env['res.users'].create({
            'name': 'HR Test Technician',
            'login': 'hr_technician',
            'email': 'hr@test.com',
        })
        
        self.technician = self.env['hr.employee'].create({
            'name': 'HR Test Technician',
            'user_id': self.technician_user.id,
            'x_inmoser_is_technician': True,
            'x_inmoser_employee_code': 'HRTECH001',
        })
        
        self.partner = self.env['res.partner'].create({
            'name': 'HR Test Customer',
        })
        
        self.equipment = self.env['inmoser.service.equipment'].create({
            'name': 'HR Test Equipment',
            'partner_id': self.partner.id,
            'equipment_type': 'computer',
        })
        
        self.service_type = self.env['inmoser.service.type'].create({
            'name': 'HR Test Service',
            'base_price': 100.0,
        })
    
    def test_timesheet_creation(self):
        """Test creación de timesheet para servicio"""
        service_order = self.env['inmoser.service.order'].create({
            'partner_id': self.partner.id,
            'equipment_id': self.equipment.id,
            'service_type_id': self.service_type.id,
            'reported_fault': 'Timesheet test',
            'assigned_technician_id': self.technician.id,
            'state': 'in_progress',
        })
        
        # Iniciar timesheet
        action = service_order.action_start_timesheet()
        
        # Verificar que se creó el timesheet
        self.assertTrue(len(service_order.timesheet_ids) > 0)
        
        timesheet = service_order.timesheet_ids[0]
        self.assertEqual(timesheet.employee_id, self.technician)
        self.assertTrue(timesheet.start_time)
        self.assertFalse(timesheet.end_time)  # Aún activo
    
    def test_timesheet_stop(self):
        """Test detener timesheet"""
        service_order = self.env['inmoser.service.order'].create({
            'partner_id': self.partner.id,
            'equipment_id': self.equipment.id,
            'service_type_id': self.service_type.id,
            'reported_fault': 'Timesheet stop test',
            'assigned_technician_id': self.technician.id,
            'state': 'in_progress',
        })
        
        # Crear timesheet activo
        timesheet = self.env['inmoser.service.timesheet'].create({
            'employee_id': self.technician.id,
            'service_order_id': service_order.id,
            'start_time': datetime.now() - timedelta(hours=2),
            'description': 'Test timesheet',
            'activity_type': 'repair',
        })
        
        # Detener timesheet
        action = service_order.action_stop_timesheet()
        
        # Verificar que se detuvo
        timesheet.refresh()
        self.assertTrue(timesheet.end_time)
        self.assertTrue(timesheet.hours > 0)
    
    def test_technician_statistics(self):
        """Test cálculo de estadísticas de técnico"""
        # Crear orden completada
        service_order = self.env['inmoser.service.order'].create({
            'partner_id': self.partner.id,
            'equipment_id': self.equipment.id,
            'service_type_id': self.service_type.id,
            'reported_fault': 'Statistics test',
            'assigned_technician_id': self.technician.id,
            'state': 'done',
            'start_date': datetime.now() - timedelta(hours=3),
            'end_date': datetime.now() - timedelta(hours=1),
            'customer_satisfaction': '5',
        })
        
        # Crear timesheet
        self.env['inmoser.service.timesheet'].create({
            'employee_id': self.technician.id,
            'service_order_id': service_order.id,
            'start_time': datetime.now() - timedelta(hours=3),
            'end_time': datetime.now() - timedelta(hours=1),
            'hours': 2.0,
            'description': 'Statistics test work',
            'activity_type': 'repair',
        })
        
        # Refrescar técnico para recalcular estadísticas
        self.technician.refresh()
        
        # Verificar estadísticas
        self.assertTrue(self.technician.total_service_hours >= 2.0)
        self.assertTrue(self.technician.avg_service_rating >= 4.0)
    
    def test_virtual_inventory(self):
        """Test inventario virtual de técnico"""
        product = self.env['product.product'].create({
            'name': 'Virtual Inventory Test Part',
            'type': 'product',
        })
        
        # Crear inventario virtual
        inventory = self.env['inmoser.technician.inventory'].create({
            'technician_id': self.technician.id,
            'product_id': product.id,
            'allocated_quantity': 10.0,
            'available_quantity': 8.0,
            'min_quantity': 2.0,
        })
        
        # Verificar cálculos
        self.assertEqual(inventory.used_quantity, 2.0)
        
        # Verificar que el técnico tiene inventario
        self.assertTrue(len(self.technician.virtual_inventory_ids) > 0)
    
    def test_technician_schedule(self):
        """Test horario de técnico"""
        # Crear horario
        schedule = self.env['inmoser.technician.schedule'].create({
            'technician_id': self.technician.id,
            'day_of_week': '1',  # Martes
            'start_time': 8.0,   # 8:00 AM
            'end_time': 17.0,    # 5:00 PM
            'max_services': 4,
        })
        
        # Verificar horario
        self.assertEqual(schedule.technician_id, self.technician)
        self.assertTrue(schedule.is_available)
        
        # Verificar que el técnico tiene horarios
        self.assertTrue(len(self.technician.service_schedule_ids) > 0)

