# -*- encoding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2011 Smile (<http://www.smile.fr>). All Rights Reserved
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

from openerp import fields
from openerp.tests.common import TransactionCase


class TestExport(TransactionCase):

    def setUp(self):
        super(TestExport, self).setUp()
        self.start_date = fields.Datetime.now()
        self.env['res.partner'].bulk_create([{'name': 'Toto %d' % x} for x in range(5)])
        self.vals = {
            'model_ids': [(6, 0, self.env.ref('base.model_res_partner').ids)],
            'start_date': self.start_date,
        }

    def test_xml_export(self):
        """
        Check that file is generated when exporting partners as XML
        """
        wizard = self.env['base.module.export'].create(dict(self.vals, filetype='xml'))
        self.assertFalse(bool(wizard.file))
        wizard.create_module()
        self.assertTrue(bool(wizard.file))

    def test_csv_export(self):
        """
        Check that file is generated when exporting partners as CSV
        """
        wizard = self.env['base.module.export'].create(dict(self.vals, filetype='csv'))
        self.assertFalse(bool(wizard.file))
        wizard.create_module()
        self.assertTrue(bool(wizard.file))
