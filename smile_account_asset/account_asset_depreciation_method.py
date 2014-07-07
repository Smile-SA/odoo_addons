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

from dateutil.relativedelta import relativedelta
import time

from osv import orm, fields
import tools
from tools.translate import _

from depreciation_board import DepreciationBoard
from account_asset_tools import get_date, get_period_stop_date, get_fiscalyear_stop_date


class AccountAssetDepreciationMethod(orm.Model):
    _name = 'account.asset.depreciation.method'
    _description = 'Asset depreciation method'

    _columns = {
        'name': fields.char('Name', size=64, required=True, translate=True),
        'code': fields.char('Code', size=32, required=True),
        'depreciation_type': fields.selection([('accounting', 'Accounting'), ('fiscal', 'Fiscal')], 'Type', required=True),
        'base_value': fields.selection([
            ('purchase_value', 'Gross Value'),
            ('book_value', 'Book Value'),
        ], 'Base', required=True),
        'use_salvage_value': fields.boolean('Take into account salvage value'),
        'depreciation_start_date': fields.selection([
            ('in_service_date', 'In-service Date'),
            ('first_day_of_purchase_month', 'First day of the month of purchase'),
        ], 'Start Date', required=True),
        'use_manual_rate': fields.boolean('Take into account depreciation rate indicated in asset'),
        'rate_formula': fields.text('Depreciation Rate', required=True,
                                    help="This expression is evaluated with length, annuity_number "
                                         "and rate (if depreciation rate indicated in asset) in localdict"),
        'prorata': fields.boolean('Prorata Temporis'),
        'need_additional_annuity': fields.boolean('Need Additional Annuity',
                                                  help="If depreciation start date is different from fiscalyear start date"),
    }

    _defaults = {
        'depreciation_start_date': 'in_service_date',
        'prorata': True,
    }

    _sql_constraints = [
        ('uniq_method', 'unique(code)', u'Method code must be unique!'),
    ]

    def _check_depreciation_rate(self, cr, uid, ids, context=None):
        for method in self.browse(cr, uid, ids, context):
            localdict = {'length': 5, 'annuity_number': 1}
            if method.use_manual_rate:
                localdict['rate'] = 35.0
            try:
                eval(method.rate_formula, localdict)
            except:
                return False
        return True

    _constraints = [
        (_check_depreciation_rate, "Bad depreciation rate formula", ['rate_formula']),
    ]

    def get_methods_selection(self, cr, uid, depreciation_type, context=None):
        assert depreciation_type in ('accounting', 'fiscal'), 'depreciation_type argument must be equal to accounting or fiscal'
        method_ids = self.search(cr, uid, [('depreciation_type', '=', depreciation_type)], context=context)
        methods = [(method['code'], method['name']) for method in self.read(cr, uid, method_ids, ['name', 'code'], context)]
        return [('none', _('None'))] + methods + [('manual', _('Manual'))]

    @tools.cache(skiparg=3)
    def get_method_infos(self, cr, uid):
        all_method_ids = self.search(cr, uid, [])
        methods = dict([(method_info['code'], method_info) for method_info in self.read(cr, uid, all_method_ids, [])])
        special_methods = {
            'none': {'name': _('None'), 'code': 'none', 'base_value': 'book_value', 'use_salvage_value': False,
                     'depreciation_start_date': 'in_service_date', 'use_manual_rate': False, 'rate_formula': '0.0',
                     'prorata': False, 'need_additional_annuity': False},
            'manual': {'name': _('Manual'), 'code': 'manual', 'base_value': 'book_value', 'use_salvage_value': False,
                       'depreciation_start_date': 'in_service_date', 'use_manual_rate': False, 'rate_formula': '0.0',
                       'prorata': False, 'need_additional_annuity': False},
        }
        methods.update(special_methods)
        return methods

    def __init__(self, pool, cr):
        super(AccountAssetDepreciationMethod, self).__init__(pool, cr)
        self.clear_caches()

    def create(self, cr, uid, vals, context=None):
        res_id = super(AccountAssetDepreciationMethod, self).create(cr, uid, vals, context)
        self.clear_caches()
        return res_id

    def write(self, cr, uid, ids, vals, context=None):
        res = super(AccountAssetDepreciationMethod, self).write(cr, uid, ids, vals, context)
        self.clear_caches()
        return res

    def _can_unlink(self, cr, uid, ids, context=None):
        if isinstance(ids, (int, long)):
            ids = [ids]
        for method in self.browse(cr, uid, ids, context):
            domain = [('%s_method' % method.depreciation_type, '=', method.code)]
            for model in ('account.asset.category', 'account.asset.asset'):
                if self.pool.get(model).search(cr, uid, domain, context=context):
                    raise orm.except_orm(_('Error'), _("You cannot unlink the method %s because it's used") % method.name)

    def unlink(self, cr, uid, ids, context=None):
        self._can_unlink(cr, uid, ids, context)
        res = super(AccountAssetDepreciationMethod, self).unlink(cr, uid, ids, context)
        self.clear_caches()
        return res

    def get_method_info(self, cr, uid, code, context=None):
        method_infos = self.get_method_infos(cr, uid)
        if code not in method_infos:
            raise orm.except_orm(_('Error'), _("Method code doesn't exist!"))
        return method_infos[code]

    def get_benefit_accelerated_depreciation(self, cr, uid, purchase_value, salvage_value, purchase_date, in_service_date,
                                             accounting_method, accounting_annuities, accounting_rate,
                                             fiscal_method, fiscal_annuities, fiscal_rate, context=None):
        first_accounting_annuity = self.compute_depreciation_board(cr, uid, accounting_method, purchase_value, salvage_value,
                                                                   accounting_annuities, accounting_rate, purchase_date, in_service_date)
        first_fiscal_annuity = self.compute_depreciation_board(cr, uid, fiscal_method, purchase_value, salvage_value,
                                                               fiscal_annuities, fiscal_rate, purchase_date, in_service_date)
        return (first_fiscal_annuity and first_fiscal_annuity[0] or 0.0) > (first_accounting_annuity and first_accounting_annuity[0] or 0.0)

    def get_depreciation_start_date(self, cr, uid, code, purchase_date, in_service_date, context=None):
        method_info = self.get_method_info(cr, uid, code, context)
        if method_info['depreciation_start_date'] == 'first_day_of_purchase_month':
            return '%s-01' % (purchase_date and purchase_date[:-3] or time.strftime('%Y-%m'))
        return in_service_date or time.strftime('%Y-%m-%d')

    def get_depreciation_stop_date(self, cr, uid, code, purchase_date, in_service_date, annuities, depreciation_period=12,
                                   fiscalyear_start_day='01-01', exceptional_values=None, context=None):
        # TODO: manage method changes history
        if code == 'none':
            return None
        method_info = self.get_method_info(cr, uid, code, context)
        date = get_date(self.get_depreciation_start_date(cr, uid, code, purchase_date, in_service_date, context))
        if not exceptional_values and method_info['need_additional_annuity']:
            date += relativedelta(years=annuities, days=-1)
            return get_period_stop_date(date, fiscalyear_start_day, depreciation_period).strftime('%Y-%m-%d')
        period_stop_date = get_fiscalyear_stop_date(date, fiscalyear_start_day)
        period_stop_date += relativedelta(years=annuities - 1)
        return period_stop_date.strftime('%Y-%m-%d')

    def compute_depreciation_board(self, cr, uid, code, purchase_value, salvage_value, annuities, rate, purchase_date, in_service_date,
                                   sale_date=None, depreciation_period=12, fiscalyear_start_day='01-01', board_stop_date=None, rounding=2,
                                   readonly_values=None, exceptional_values=None, context=None):
        if code == 'none':
            return []
        kwargs = locals().copy()
        kwargs['method_info'] = self.get_method_info(cr, uid, code, context)
        kwargs['depreciation_start_date'] = self.get_depreciation_start_date(cr, uid, code, purchase_date, in_service_date, context)
        for key in ('self', 'cr', 'uid', 'code', 'purchase_date', 'in_service_date', 'context'):
            del kwargs[key]
        board = DepreciationBoard(**kwargs)
        return [line.__dict__ for line in board.compute()]
