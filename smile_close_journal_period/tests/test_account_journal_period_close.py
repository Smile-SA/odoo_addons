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

from datetime import datetime

import openerp.tests.common as common


def get_simple_account_move_values(self, period_id, journal_id, account_id, cash_account_id):
    return {'period_id': period_id.id,
            'date': period_id.date_start,
            'journal_id': journal_id.id,
            'line_id': [(0, 0, {'name': 'test',
                                'account_id': cash_account_id.id,
                                'debit': 50.0,
                                }),
                        (0, 0, {'name': 'test_conterpart',
                                'account_id': account_id.id,
                                'credit': 50.0,
                                })
                        ]
            }


class TestAccountJournalPeriodClose(common.TransactionCase):

    def setUp(self):
        super(TestAccountJournalPeriodClose, self).setUp()
        self.jour_per_obj = self.env['account.journal.period']
        fiscalyear_obj = self.env['account.fiscalyear']
        company_id = self.ref('base.main_company')
        today = datetime.now().date()
        last_year = today.replace(year=datetime.now().date().year-1)
        year = last_year.strftime('%Y')

        # 1 Get journal_id & account_ids
        self.journal_id = self.env['account.journal'].search([('type', '=', 'purchase')], limit=1)[0]
        self.account_id = self.env['account.account'].search([('type', '=', 'other')], limit=1)[0]
        self.cash_account_id = self.env['account.account'].search([('type', '=', 'liquidity')], limit=1)[0]
        # 2 Create Fiscal Year
        self.fiscalyear_id = fiscalyear_obj.create({
            'name': year + 'DEMO',
            'code': year + 'DEMO',
            'date_start': year + '-01-01',
            'date_stop': year + '-12-31',
            'company_id': company_id
        })
        # 3 Create Periods
        self.fiscalyear_id.create_period()
        self.period_id = self.env['account.period'].search([('fiscalyear_id', '=', self.fiscalyear_id.id)], limit=1)[0]

    def test_close_journal_close_period(self):
        # 1 Create Move
        print "########################## Create Account Move #############################"
        move_values = get_simple_account_move_values(self, self.period_id, self.journal_id, self.account_id, self.cash_account_id)
        self.env['account.move'].create(move_values)
        # 2 Close Journal Period
        print "########################## Close Journal Period #############################"
        journal_period_ids = self.jour_per_obj.search([('period_id', '=', self.period_id.id), ('journal_id', '=', self.journal_id.id)])
        journal_period_ids[0].action_done()
        # 3 Close Period
        print "########################## Close Period #############################"
        close_period_wizard_id = self.env['account.period.close'].create({'sure': True})
        active_ids = {'active_ids': [self.period_id.id]}
        close_period_wizard_id.with_context(active_ids).data_save()
