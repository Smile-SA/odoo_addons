# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2014 Smile (<http://www.smile.fr>).
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

from openerp import fields
from openerp.exceptions import UserError, ValidationError
from openerp.tests.common import TransactionCase


class TestProductOption(TransactionCase):

    def setUp(self):
        super(TestProductOption, self).setUp()
        self.product = self.env.ref('product.product_product_8')
        partner = self.env.ref('base.res_partner_2')
        self.sale_order = self.env['sale.order'].create({
            'partner_id': partner.id,
            'partner_invoice_id': partner.id,
            'partner_shipping_id': partner.id,
            'user_id': self.env.uid,
            'pricelist_id': self.env.ref('product.list0').id,
            'team_id': self.env.ref('sales_team.team_sales_department').id,
            'date_order': fields.Date.today(),
        })

    def create_sale_order_line(self, context=None):
        context = context or {}
        return self.env['sale.order.line'].with_context(**context).create({
            'order_id': self.sale_order.id,
            'product_id': self.product.id,
        })

    def test_10_sale_order_lines_number(self):
        """
        1. I create a quotation for an iMac (without add_all_options in context)
        2. I check the number of lines (2 = 1 iMac + 1 mandatory option)
        3. I check the number of visible lines (1 because the option keyboard is hidden in sale order)
        """
        self.create_sale_order_line()
        self.assertEquals(len(self.sale_order.order_line), 2)
        self.assertEquals(len(self.sale_order.visible_line_ids), 1)

    def test_20_sale_order_lines_number(self):
        """
        1. I add again an iMac (with add_all_options in context)
        2. I check the number of lines (5 = 1 iMac + 4 options)
        3. I check the number of visible lines (4 because the option keyboard is hidden in sale order)
        """
        self.create_sale_order_line({'add_all_options': True})
        self.assertEquals(len(self.sale_order.order_line), 5)
        self.assertEquals(len(self.sale_order.visible_line_ids), 4)

    def get_line(self, quantity_type):
        return self.sale_order.order_line.filtered(lambda line: line.quantity_type == quantity_type)

    def test_30_sale_order_lines_quantity(self):
        """
        1. I add again an iMac (with add_all_options in context)
        2. I modify the quantity of an option with a free quantity
        3. I check the quantity changed
        4. I modify the quantity of an option with a fixed quantity
        5. I check an exception is raised
        6. I modify the quantity of an option with a quantity multiple of main product
        7. I check an exception is raised if the new quantity is not a multiple
        8. I check the quantity changed if the new quantity is a multiple
        9. I modify the quantity of an option with a quantity identical to main product
        10. I check an exception is raised
        """
        self.create_sale_order_line({'add_all_options': True})
        free_line = self.get_line('free')
        free_line.product_uom_qty = 2
        self.assertEquals(free_line.product_uom_qty, 2)
        fixed_line = self.get_line('fixed')
        with self.assertRaises(UserError):
            fixed_line.product_uom_qty = 2
        multiple_line = self.get_line('free_and_multiple')
        with self.assertRaises(ValidationError):
            multiple_line.product_uom_qty = 1.5
        multiple_line.product_uom_qty = 2
        self.assertEquals(multiple_line.product_uom_qty, 2)
        identical_line = self.get_line('identical')
        with self.assertRaises(ValidationError):
            identical_line.product_uom_qty = 2

    def test_40_sale_order_lines_price(self):
        """
        1. I create a quotation for an iMac (without add_all_options in context)
        2. I check the visible unit price of iMax is equals to 1799 (because keyboard is hidden in sale order)
        3. I check the visible unit price of keyboard is equals to 47
        4. I check the unit price of iMax is equals to 1752 (iMac - keyboard because this option is included in price)
        5. I check the unit price of keyboard is equals to 47
        """
        self.create_sale_order_line()
        iMac = self.sale_order.order_line.filtered(lambda line: line.product_id == self.product)
        keyboard = self.sale_order.order_line.filtered(lambda line: line.is_mandatory)
        self.assertEquals(iMac.visible_price_unit, 1799.0)
        self.assertEquals(keyboard.visible_price_unit, 47.0)
        self.assertEquals(iMac.price_unit, 1752.0)
        self.assertEquals(keyboard.price_unit, 47.0)

    def test_50_sale_order_lines_deletion(self):
        """
        1. I create a quotation for an iMac (without add_all_options in context)
        2. I delete the line linked to mandatory option
        3. I check a exception is raised
        4. I delete the line linked to iMac
        5. I check the 2 lines were removed
        """
        self.create_sale_order_line()
        with self.assertRaises(UserError):
            self.sale_order.order_line[-1].unlink()
        self.sale_order.order_line[0].unlink()
        self.assertEquals(len(self.sale_order.order_line), 0)

    def test_60_sale_order_lines_sequence(self):
        """
        1. I add an iMac (with add_all_options in context)
        2. I add an iPad
        3. I check the number of lines (6 = 5 previous + 1 iPad)
        4. I check the number of visible lines (5 = 4 previous + 1 iPad)
        5. I place iPad in third position
        6. I check iPad is in last position, ie after iMac and its options
        7. I place iPad in first position
        8. I check iPad is really in first position
        """
        self.create_sale_order_line({'add_all_options': True})
        new_line = self.env['sale.order.line'].create({
            'order_id': self.sale_order.id,
            'product_id': self.env.ref('product.product_product_6').id,
        })
        self.assertEquals(len(self.sale_order.order_line), 6)
        self.assertEquals(len(self.sale_order.visible_line_ids), 5)

        self.sale_order.write({
            'visible_line_ids': [(1, new_line.id, {'sequence': self.sale_order.visible_line_ids[2].sequence})],
        })
        self.assertEquals(new_line.sequence, max(self.sale_order.visible_line_ids.mapped('sequence')))

        self.sale_order.write({
            'order_line': [(1, new_line.id, {'sequence': self.sale_order.visible_line_ids[0].sequence - 1})],
        })
        self.assertEquals(new_line.sequence, min(self.sale_order.visible_line_ids.mapped('sequence')))

    def test_70_account_invoice_lines(self):
        """
        1. I add again an iMac (with add_all_options in context)
        2. I confirm the quotation
        3. I specify delivered quantities for iMac
        4. I check the delivered quantities for keyboard is identical to iMac
            (because the option keyboard is hidden in sale order and delivered quantity updateable)
        5. I create the customer invoice
        6. I check the number of customer invoice lines (3 because the option antivirus is a service)
        7. I check the number of visible invoice lines (3 because the option keyboard is not hidden in customer invoice)
        8. I check the visible unit price of iMax is equals to 1752 (because keyboard is visible in customer invoice)
        9. I check the visible unit price of keyboard is equals to 47
        10. I check the unit price of iMax is equals to 1752
        11. I check the unit price of keyboard is equals to 47
        """
        self.create_sale_order_line({'add_all_options': True})
        self.sale_order.action_confirm()
        self.assertEquals(self.sale_order.state, 'sale')

        line = self.sale_order.order_line.filtered(lambda line: line.product_id == self.product)
        line.qty_delivered = line.product_uom_qty
        invoice = self.env['account.invoice'].browse(self.sale_order.action_invoice_create())
        self.assertEquals(len(invoice.invoice_line_ids), 3)
        self.assertEquals(len(invoice.visible_line_ids), 3)

        iMac = invoice.invoice_line_ids.filtered(lambda line: line.product_id == self.product)
        keyboard = invoice.invoice_line_ids.filtered(lambda line: line.is_mandatory)
        self.assertEquals(iMac.visible_price_unit, 1752.0)
        self.assertEquals(keyboard.visible_price_unit, 47.0)
        self.assertEquals(iMac.price_unit, 1752.0)
        self.assertEquals(keyboard.price_unit, 47.0)
