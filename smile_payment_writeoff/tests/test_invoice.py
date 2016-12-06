# -*- encoding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2016 Smile (<http://www.smile.fr>). All Rights Reserved
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

from openerp.tests.common import TransactionCase


class TestAutomaticPaymentWriteoff(TransactionCase):

    def setUp(self):
        super(TestAutomaticPaymentWriteoff, self).setUp()

        user_values = {'name': 'User Test',
                       'login': 'user_test',
                       'groups_id': [(6, 0, [self.env.ref('account.group_account_invoice').id])],
                       'email': 'user_test@mail.com', }
        self.user = self.env['res.users'].create(user_values)
        product_vals = {'name': 'Product',
                        'type': 'consu',
                        'list_price': 50,
                        'sale_ok': True, }
        self.product = self.env['product.product'].create(product_vals)
        self.env.ref('base.main_company').invoice_loss_amount = 2
        self.env.ref('base.main_company').invoice_profit_amount = 1
        account = self.env['account.account'].search([('code', '=', '658000')], limit = 1)
        if not account:
            account_values = {'name': 'Charges diverses de gestion courante',
                              'code': '658000',
                              'internal_type': 'other',
                              'user_type_id': self.env.ref('account.data_account_type_expenses').id, }
            account = self.env['account.account'].create(account_values)
        self.env.ref('base.main_company').invoice_loss_account_id = account
        account = self.env['account.account'].search([('code', '=', '758000')], limit = 1)
        if not account:
            account_values = {'name': 'Produits divers de gestion courante',
                              'code': '758000',
                              'internal_type': 'other',
                              'user_type_id': self.env.ref('account.data_account_type_revenue').id, }
            account = self.env['account.account'].create(account_values)
        self.env.ref('base.main_company').invoice_profit_account_id = account
        self.customer_account = self.env['account.account'].search([('code', '=', '411100')], limit = 1)
        if not self.customer_account:
            customer_account_values = {'name': 'Clients - Ventes de biens ou de prestations de services',
                                       'code': '411100',
                                       'internal_type': 'receivable',
                                       'user_type_id': self.env.ref('account.data_account_type_receivable'), }
            self.customer_account = self.env['account.account'].create(customer_account_values)

    def create_payment(self, customer, invoice, amount):
        payment_methods = invoice.journal_id.inbound_payment_method_ids
        payment_values = {'payment_type': 'inbound',
                          'partner_type': 'customer',
                          'partner_id': customer.id,
                          'journal_id': invoice.journal_id.id,
                          'payment_method_id': payment_methods[0].id,
                          'invoice_ids': [(6, 0, [invoice.id])],
                          'amount': amount, }
        payment = self.env['account.payment'].create(payment_values)
        payment.sudo(self.user.id).onchange_writeoff_amount()
        return payment

    def create_invoice_line(self, invoice):
        invoice_line_values = {'name': self.product.name,
                               'invoice_id': invoice.id,
                               'product_id': self.product.id,
                               'price_unit': 50.00,
                               'account_id': invoice.journal_id.default_credit_account_id.id,
                               'quantity': 1, }
        self.env['account.invoice.line'].sudo(self.user.id).create(invoice_line_values)

    def check_move_line(self, move_id, nb_lines, amount=None, acc_number=None):
        """
        move_id est redéfini comme étant l'écriture comptable contenant la ligne lettrée avec la ligne de la facture.
        Cette fonction permet de tester :
        * Si les nb_lines est égal au nombre de lignes de l'écriture comptable move_id
        * Vérifie qu'il existe une unique ligne de l'écriture comptable move_id avec comme crébit (si amount est
          positif) ou comme crédit (si amount est négatif) amount et comme compte celui ayant comme code acc_number
        """
        reconcile_line_id = move_id.line_ids.filtered(lambda l: l.debit > 0 and l.full_reconcile_id)
        self.assertEqual(len(reconcile_line_id), 1)
        line_id = reconcile_line_id.full_reconcile_id.reconciled_line_ids.filtered(lambda l: l != reconcile_line_id)
        move_id = line_id.move_id
        self.assertEqual(len(move_id.line_ids), nb_lines)
        if amount > 0:
            lines = move_id.line_ids.filtered(lambda l: l.account_id.code == acc_number and l.credit == amount)
        else:
            lines = move_id.line_ids.filtered(lambda l: l.account_id.code == acc_number and l.debit == amount * -1)
        self.assertEqual(len(lines), 1)

    def test_00_automatic_paid_invoice(self):
        """
        Utilisateur : User Test
        Paramétrage sur la société :
          * écart perte : 2,00€
          * écart profit : 1,00€
          * compte perte : 658000
          * compte profit : 758000
        1 - Création de 5 client. Création de 1 facture pour chacun des 5 clients, avec comme article product (quantité
            1, prix unitaire 50€). Validation des factures.
        2 - Création d'un paiement de 50,00€ pour la facture 1. La facture doit être payée.
        3 - Création d'un paiement de 50,50€ pour la facture 2. La facture doit être payée. L'écriture comptable à trois
            lignes dont une correspond à l'écart (crédit de 0,50€ sur le compte 758000).
        4 - Création d'un paiement de 48,50€ pour la facture 3. La facture doit être payée. L'écriture comptable à trois
            lignes dont une correspond à l'écart (débit de 1,50€ sur le compte 658000).
        5 - Création d'un paiement de 51,00€ pour la facture 4. La facture doit être payée.
        6 - Création d'un paiement de 48,00€ pour la facture 5. La facture doit être ouverte.
        """
        # 1
        customers = self.env['res.partner']
        invoices = self.env['account.invoice']
        for x in range(0, 5):
            customer_values = {'name': 'Customer ' + str(x),
                               'customer': True, }
            customers += self.env['res.partner'].create(customer_values)
            invoice_values = {'partner_id': customers[x].id,
                              'account_id': self.customer_account.id, }
            invoices += self.env['account.invoice'].sudo(self.user.id).create(invoice_values)
            self.create_invoice_line(invoices[x])
            invoices[x].sudo(self.user.id).action_invoice_open()
        cnt = 0
        # 2
        payment = self.create_payment(customers[cnt], invoices[cnt], 50)
        payment.sudo(self.user.id).post()
        self.assertEqual(invoices[cnt].state, 'paid')
        cnt += 1
        # 3
        payment = self.create_payment(customers[cnt], invoices[cnt], 50.5)
        payment.sudo(self.user.id).post()
        self.assertEqual(invoices[cnt].state, 'paid')
        self.check_move_line(invoices[cnt].move_id, 3, 0.5, '758000')
        cnt += 1
        # 4
        payment = self.create_payment(customers[cnt], invoices[cnt], 48.5)
        payment.sudo(self.user.id).post()
        self.assertEqual(invoices[cnt].state, 'paid')
        self.check_move_line(invoices[cnt].move_id, 3, -1.5, '658000')
        cnt += 1
        # 5
        payment = self.create_payment(customers[cnt], invoices[cnt], 51)
        payment.sudo(self.user.id).post()
        self.assertEqual(invoices[cnt].state, 'paid')
        cnt += 1
        # 6
        payment = self.create_payment(customers[cnt], invoices[cnt], 48)
        payment.sudo(self.user.id).post()
        self.assertEqual(invoices[cnt].state, 'open')
