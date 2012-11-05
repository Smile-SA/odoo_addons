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

from osv import orm, fields
from tools.translate import _


class ResCompany(orm.Model):
    _inherit = 'res.company'

    _columns = {
        'fiscal_depreciation_account_id': fields.many2one('account.account', 'Fiscal Depreciation Account', required=False, ondelete='restrict'),
        'fiscal_depreciation_expense_account_id': fields.many2one('account.account', 'Fiscal Depreciation Expense Account',
                                                                  required=False, ondelete='restrict'),
        'fiscal_depreciation_income_account_id': fields.many2one('account.account', 'Fiscal Depreciation Income Account',
                                                                 required=False, ondelete='restrict'),
    }

    def get_fiscalyear_start_day(self, cr, uid, company_id, context=None):
        assert isinstance(company_id, (int, long)), 'company_id must be an integer'
        context_copy = (context or {}).copy()
        context_copy['company_id'] = company_id
        fiscalyear_obj = self.pool.get('account.fiscalyear')
        fiscalyear_id = fiscalyear_obj.find(cr, uid, context=context_copy)
        if not fiscalyear_id:
            company_name = self.name_get(cr, uid, [company_id], context)[0][1]
            raise orm.except_orm(_('Error'), _('Please create a fiscal year for the company %s') % company_name)
        fiscalyear = fiscalyear_obj.read(cr, uid, fiscalyear_id, ['date_start'], context)
        return fiscalyear['date_start'][5:]
