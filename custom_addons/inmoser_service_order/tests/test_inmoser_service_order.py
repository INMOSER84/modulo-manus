# -*- coding: utf-8 -*-
from odoo.tests.common import TransactionCase

class TestInmoserServiceOrder(TransactionCase):
    
    def setUp(self):
        super().setUp()
        self.ServiceOrder = self.env['inmoser.service.order']
        self.Partner = self.env['res.partner']
        self.Equipment = self.env['inmoser.service.equipment']
        self.ServiceType = self.env['inmoser.service.type']

        self.partner_test = self.Partner.create({
            'name': 'Test Partner',
        })
        self.equipment_test = self.Equipment.create({
            'name': 'Test Equipment',
            'partner_id': self.partner_test.id,
        })
        self.service_type_test = self.ServiceType.create({
            'name': 'Test Service Type',
        })
    
    def test_create_service_order(self):
        # Test básico de creación
        order = self.ServiceOrder.create({
            'name': 'Test OS',
            'partner_id': self.partner_test.id,
            'equipment_id': self.equipment_test.id,
            'service_type_id': self.service_type_test.id,
        })
        self.assertTrue(order.name.startswith('OS'))
