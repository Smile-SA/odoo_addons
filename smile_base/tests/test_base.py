# -*- encoding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2013 Smile (<http://www.smile.fr>). All Rights Reserved
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


class BaseTest(TransactionCase):

    def setUp(self):
        super(BaseTest, self).setUp()
        self.model = self.env['res.partner.category']

    def test_bulk_create(self):
        names = ['t1', 't2', 't3']
        vals_list = [{'name': name} for name in names]
        categories = self.model.bulk_create(vals_list)
        self.assertEquals(3, len(categories), 'Three categories shoudl have been created!')
        self.assertListEqual(names, sorted(categories.mapped('name')),
                             'Names of the created categories are wrong!')

    def test_unlink_cascade(self):
        parent = self.model.create({'name': 'Parent'})
        child = self.model.create({'name': 'Child', 'parent_id': parent.id})
        self.assertTrue(parent.unlink())
        self.assertFalse(child.exists())
