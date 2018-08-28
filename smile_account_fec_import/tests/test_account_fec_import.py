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

import base64
import os

from openerp import tools
from openerp.tests.common import TransactionCase

SAMPLE_FEC = 'sample_fec.txt'


class TestAccountFecImport(TransactionCase):

    def setUp(self):
        super(TestAccountFecImport, self).setUp()
        self._journal = self.env['account.journal'].create({'code': 'TEST', 'name': 'Test', 'type': 'bank',
                                                            'sequence_id': self.env.ref('account.sequence_bank_journal').id})

    def _get_file(self, filename):
        for path in tools.config['addons_path'].split(','):
            dirpath = os.path.join(path, *self.__module__.split('.')[2:-1])
            filepath = os.path.join(dirpath, filename)
            if not os.path.isfile(filepath):
                continue
            with open(filepath) as f:
                return base64.b64encode(f.read())
        return False

    def test_account_fec_import(self):
        wizard = self.env['account.fr.fec.import'].create({
            'fec_file': self._get_file(SAMPLE_FEC),
            'account_journal_ids': [(6, 0, self._journal.ids)],
            'import_reconciliation': True,
            'delimiter': '\t',
        })
        wizard.import_file()
        move = self.env['account.move'].search([('ref', '=', 'TEST_10')])
        self.assertEquals(True, bool(move), 'Account move not imported')
        self.assertEquals(3, len(move.line_id), 'Account move lines not all imported')
        self.assertEquals('2014-04-01', move.date, 'Imported account move has wrong date')
        self.assertEquals(23409.58, move.amount, 'Imported account move has wrong amount')
        self.assertEquals('posted', move.state, 'Imported account move not posted')
