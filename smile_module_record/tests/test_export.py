# -*- coding: utf-8 -*-
# (C) 2011 Smile (<http://www.smile.fr>)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields
from odoo.tests.common import TransactionCase


class TestExport(TransactionCase):

    def setUp(self):
        super(TestExport, self).setUp()
        self.start_date = fields.Datetime.now()
        self.env['res.partner'].create(
            [{'name': 'Toto %d' % x} for x in range(5)])
        self.vals = {
            'model_ids': [(6, 0, self.env.ref('base.model_res_partner').ids)],
            'start_date': self.start_date,
        }

    def test_xml_export(self):
        """
        Check that file is generated when exporting partners as XML
        """
        wizard = self.env['base.module.export'].create(
            dict(self.vals, filetype='xml'))
        self.assertFalse(bool(wizard.file))
        wizard.create_module()
        self.assertTrue(bool(wizard.file))

    def test_csv_export(self):
        """
        Check that file is generated when exporting partners as CSV
        """
        wizard = self.env['base.module.export'].create(
            dict(self.vals, filetype='csv'))
        self.assertFalse(bool(wizard.file))
        wizard.create_module()
        self.assertTrue(bool(wizard.file))
