# -*- encoding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2012 Smile (<http://www.smile.fr>). All Rights Reserved
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

import time

from osv import orm, fields


class ResCompany(orm.Model):
    _inherit = 'res.company'

    _columns = {
        'depreciation_period': fields.selection([(1, 'Monthly'), (2, 'Bimonthly'), (3, '3-Monthly'), (4, '4-Monthly'),
                                                 (6, 'Halfyearly'), (12, 'Yearly')], 'Depreciation Frequency', required=True),
        'fiscal_depreciation_account_id': fields.many2one('account.account', 'Fiscal Depreciation Account', required=False,
                                                          ondelete='restrict'),
        'fiscal_depreciation_expense_account_id': fields.many2one('account.account', 'Fiscal Depreciation Expense Account',
                                                                  required=False, ondelete='restrict'),
        'fiscal_depreciation_income_account_id': fields.many2one('account.account', 'Fiscal Depreciation Income Account',
                                                                 required=False, ondelete='restrict'),
        'exceptional_amortization_expense_account_id': fields.many2one('account.account', 'Exceptional Depreciation Expense Account',
                                                                       required=False, ondelete='restrict',
                                                                       help="Use for transfer depreciations in amortizations"),
        'exceptional_amortization_income_account_id': fields.many2one('account.account', 'Exceptional Depreciation Income Account',
                                                                      required=False, ondelete='restrict',
                                                                      help="Use for transfer depreciations in amortizations"),
    }

    _defaults = {
        'depreciation_period': 12,
    }

    def get_fiscalyear_start_day(self, cr, uid, company_id, context=None):
        assert isinstance(company_id, (int, long)), 'company_id must be an integer'
        context_copy = context and context.copy() or {}
        context_copy['company_id'] = company_id
        fiscalyear_obj = self.pool.get('account.fiscalyear')
        fiscalyear_id = fiscalyear_obj.find(cr, uid, context=context_copy)
        if fiscalyear_id:
            return fiscalyear_obj.read(cr, uid, fiscalyear_id, ['date_start'], context)['date_start'][5:]
        return '01-01'

    def get_fiscalyear(self, cr, uid, company_id, date=None, context=None):
        if isinstance(company_id, list):
            company_id = company_id[0]
        if not date:
            date = time.strftime('%Y-%m-%d')
        year = int(date[:4])
        fiscalyear_start_day = self.get_fiscalyear_start_day(cr, uid, company_id, context)
        if date[5:] < fiscalyear_start_day:
            year += 1
        return str(year)

    def write(self, cr, uid, ids, vals, context=None):
        if isinstance(ids, (int, long)):
            ids = [ids]
        for company_id in ids:
            old_vals = self.read(cr, uid, company_id, vals.keys(), context, '_classic_write')
            del old_vals['id']
            self.pool.get('account.asset.asset').change_accounts(cr, uid, '%s,%s' % (self._name, company_id), old_vals, vals, context)
        return super(ResCompany, self).write(cr, uid, ids, vals, context)
