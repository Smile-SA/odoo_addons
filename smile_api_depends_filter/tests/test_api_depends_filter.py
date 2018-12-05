# -*- coding: utf-8 -*-
# (C) 2018 Smile (<http://www.smile.fr>)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo.tests.common import TransactionCase


class ApiDependsFilter(TransactionCase):

    def test_api_depends_filter(self):
        TestModel = self.env['ir.model.test']
        record1 = TestModel.create({'name': 'Record 1', 'state': 'draft'})
        record2 = TestModel.create({'name': 'Record 2', 'state': 'done'})
        (record1 | record2).write({'name': 'New name'})
        self.assertEquals(record1.copy_name, record1.name)
        self.assertNotEquals(record2.copy_name, record2.name)
