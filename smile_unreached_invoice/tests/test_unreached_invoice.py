# Copyright 2023 Smile
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).


from odoo import fields
from odoo.tests.common import TransactionCase
from odoo.exceptions import AccessError


class TestUnreachedInvoice(TransactionCase):

    def setUp(self):
        super(TestUnreachedInvoice, self).setUp()
        self.AccountAccount = self.env['account.account']
        self.AccountUnreachedInvoice = self.env['smile.unreached.invoice']
        self.PurchaseOrder = self.env['purchase.order']
        self.AccountJournal = self.env['account.journal']

        self.account_credit_id = self.AccountAccount.search([], limit=1)
        self.account_debit_id = self.AccountAccount.search([], limit=1, offset=1)
        self.journal_id = self.AccountJournal.search([], limit=1)

        self.partner = self.env['res.partner'].create({'name': 'Example Supplier'})
        self.product = self.env['product.product'].create({'name': 'Example Product'})
        self.product_uom = self.env['uom.uom'].search([], limit=1)
        self.user_demo = self.env['res.users'].create({
            'name': 'Demo User',
            'login': 'demo_user',
            'email': 'demo_user@example.com',
            'password': 'demo_user_password',
        })

    def test_account_unreached_invoice_access(self):
        """
            Verify if the user can access the action account_unreached_invoice_act_window
        """
        with self.assertRaises(AccessError):
            self.AccountUnreachedInvoice.with_user(self.user_demo).create({})

    def test_account_unreached_invoice_generate(self):
        """
            Test that account moves are generated and reversed correctly when
            a purchase order is confirmed and invoiced using the account.unreached.invoice wizard.
        """

        reversal_date = fields.Date.from_string('2023-03-24')
        accouting_date = fields.Date.from_string('2023-03-23')

        # Add the user to the group account_user
        group_account_user = self.env.ref('account.group_account_user')
        self.user_demo.groups_id = [(6, 0, [group_account_user.id])]

        # Create a purchase order
        purchase_order_values = {
            'partner_id': self.partner.id,
            'date_order': '2023-03-23',
            'order_line': [
                (0, 0, {
                    'product_id': self.product.id,
                    'product_qty': 5,
                    'product_uom': self.product_uom.id,
                    'price_unit': 100.0,
                    'name': 'Example Product',
                    'date_planned': '2023-03-30',
                }),
            ],
        }
        purchase_order = self.PurchaseOrder.create(purchase_order_values)

        # Confirm and receive the purchase order
        purchase_order.button_confirm()
        order_line = purchase_order.order_line[0]
        order_line.qty_received = 5

        # Create an instance of the account.unreached.invoice wizard
        ctx = {
            'active_model': 'purchase.order',
            'active_ids': [purchase_order.id],
        }
        wizard = self.AccountUnreachedInvoice.with_context(ctx).create({
            'accounting_date': accouting_date,
            'account_credit_id': self.account_credit_id.id,
            'account_debit_id': self.account_debit_id.id,
            'journal_id': self.journal_id.id,
            'reversal_date': reversal_date,
        })

        # Call the generate() method of the account.unreached.invoice wizard
        action = wizard.generate()

        # Check the result of the generate() method
        self.assertTrue(action, "The method 'generate' should return an action")
        self.assertIn('domain', action, "The result should contain a domain")

        moves_ids = self.env['account.move'].search(action['domain']).ids

        self.assertEqual(len(moves_ids), 2, "Two moves should be generated")
        for move_id in moves_ids:
            move = self.env['account.move'].browse(move_id)
            reversal_entry = move.reversed_entry_id
            move_date = move.date

            if reversal_entry:
                self.assertEqual(reversal_entry.id, moves_ids[1], "The reverse entry should be the first move")
                self.assertEqual(move_date, reversal_date, "The move date should be equal to the reversal date")
            else:
                self.assertEqual(move_date, accouting_date, "The move date should be equal to the accounting date")
            self.assertTrue(move.line_ids, "The moves should have lines")
            self.assertTrue(move.line_ids.filtered(
                lambda line: line.account_id == self.account_credit_id),
                "One move should be credited to the account_credit_id",
            )
            self.assertTrue(move.line_ids.filtered(
                lambda line: line.account_id == self.account_debit_id),
                "One move should be debited to the account_debit_id",
            )
