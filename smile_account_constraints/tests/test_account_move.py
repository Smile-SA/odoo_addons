# -*- encoding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2015 Smile (<http://www.smile.fr>). All Rights Reserved
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

import openerp.tests.common as common


class test_account_move(common.TransactionCase):

    def setUp(self):
        super(test_account_move, self).setUp()
        self.acc_move = self.env['account.move']

        # 1 Get journal_id & period_id & account_ids
        self.journal_id = self.env['account.journal'].search([('type', '=', 'purchase')], limit=1)[0]
        self.account_id = self.env['account.account'].search([('type', '=', 'other')], limit=1)[0]
        self.cash_account_id = self.env['account.account'].search([('type', '=', 'liquidity')], limit=1)[0]
        self.period_id = self.env['account.period'].search([('state', '=', 'draft')], limit=1)[0]

    def test_post_account_move(self):
        import logging
        LOGGER = logging.getLogger('account.move')

        vals = {'period_id': self.period_id.id,
                'date': self.period_id.date_start,
                'journal_id': self.journal_id.id,
                'line_id': [(0, 0, {'name': 'test',
                                    'account_id': self.cash_account_id.id,
                                    'debit': 0.0,
                                    'credit': 0.0})]
                }
        # 1 Create Move, it calls post move
        create_ok = False
        try:
            create_ok = self.acc_move.create(vals)
        except Exception, e:
            LOGGER.info("=================>#EXCEPTION........ %s" % e)
            pass
        self.assertFalse(create_ok)

        vals1 = {'period_id': self.period_id.id,
                 'date': self.period_id.date_start,
                 'journal_id': self.journal_id.id,
                 'line_id': [(0, 0, {'name': 'test',
                                     'account_id': self.cash_account_id.id,
                                     'debit': 10.0}),
                             (0, 0, {'name': 'test',
                                     'account_id': self.account_id.id,
                                     'credit': 10.0})]
                 }
        # 1 Create Move, Posted OK
        move_id = False
        try:
            move_id = self.acc_move.create(vals1)
            print "########## Account Move State ###########", move_id.state
        except Exception, e:
            LOGGER.info("=================>#EXCEPTION........ %s" % e)
            pass
        self.assertTrue(move_id)
