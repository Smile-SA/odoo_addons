# -*- coding: utf-8 -*-
# (C) 2019 Smile (<http://www.smile.fr>)
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl).

from odoo.tests.common import TransactionCase


class TestEventRegistration(TransactionCase):

    def setUp(self):
        super(TestEventRegistration, self).setUp()

        self.EventRegistration = self.env['event.registration']

        # First I create an event product
        product = self.env['product.product'].create({
            'name': 'test_formation',
            'type': 'service',
            'event_ok': True,
        })

        # I create an event from the same type than my product
        event = self.env['event.event'].create({
            'name': 'test_event',
            'event_type_id': 1,
            'date_end': '2012-01-01 19:05:15',
            'date_begin': '2012-01-01 18:05:15'
        })

        ticket = self.env['event.event.ticket'].create({
            'name': 'test_ticket',
            'product_id': product.id,
            'event_id': event.id,
        })

        # I create a sales order
        self.sale_order = self.env['sale.order'].create({
            'partner_id': self.env.ref('base.res_partner_2').id,
            'note': 'Invoice after delivery',
            'payment_term_id': self.env.ref('account.account_payment_term').id
        })

        # In the sales order I add some sales order lines. i choose
        # event product
        self.env['sale.order.line'].create({
            'product_id': product.id,
            'price_unit': 190.50,
            'product_uom': self.env.ref('uom.product_uom_unit').id,
            'product_uom_qty': 8.0,
            'order_id': self.sale_order.id,
            'name': 'sales order line',
            'event_id': event.id,
            'event_ticket_id': ticket.id,
        })

        # In the event registration I add some attendee detail lines. i choose
        # event product
        self.register_person = self.env['registration.editor'].create({
            'sale_order_id': self.sale_order.id,
            'event_registration_ids': [(0, 0, {
                'event_id': event.id,
                'name': 'Administrator',
                'email': 'abc@example.com'
            })],
        })
        self.register_person.action_make_registration()
        self.registration = self.EventRegistration.search(
            [('origin', '=', self.sale_order.name)])
        self.sale_order.action_confirm()
        context = {
            'active_model': 'sale.order',
            'active_ids': [self.sale_order.id],
            'active_id': self.sale_order.id,
        }
        payment = self.env['sale.advance.payment.inv'].with_context(
            context).create({})
        # Create draft invoice to sale order
        payment.create_invoices()
        self.invoice = self.sale_order.invoice_ids

    def test_01_cancel_and_refund_event_registration_to_cancel(self):
        """
              Check cancel & refund  event registration
        """
        self.registration.button_cancel_refund()
        self.assertEqual(
            self.registration.state, 'cancel', 'Registration should be cancel')

    def test_02_cancel_and_refund_event_registration_to_refund(self):
        """
              Check cancel & refund  event registration
        """
        self.invoice.action_invoice_open()
        self.registration.button_cancel_refund()
        self.assertEqual(
            self.registration.state, 'refund', 'Registration should be Refund')

    def test_03_cancel_and_refund_event_to_cancel(self):
        """
              Check cancel & refund event to cancel
        """
        event_refund = self.env['event.refund'].create({'event_id': '1'})
        event_refund.button_cancel_without_refund()
        self.assertEqual(
            event_refund.event_id.state, 'cancel', 'Event should be Cancel')
