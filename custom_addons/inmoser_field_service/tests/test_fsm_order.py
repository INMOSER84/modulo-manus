# tests/test_fsm_order.py
from odoo.tests import TransactionCase

class TestFSMOrder(TransactionCase):
    def setUp(self):
        super().setUp()
        self.FSMOrder = self.env['fsm.order']
    
    def test_create_fsm_order(self):
        """Test FSM order creation"""
        order = self.FSMOrder.create({
            'name': 'Test Order',
        })
        self.assertTrue(order)
