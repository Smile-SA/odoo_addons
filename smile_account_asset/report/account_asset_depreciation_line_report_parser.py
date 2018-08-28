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

from datetime import datetime
from dateutil.relativedelta import relativedelta
import time

from osv import orm
from report import report_sxw
from tools.translate import _

from openerp.addons.smile_account_asset.account_asset_tools import get_period_stop_date


class AccountAssetDepreciationLineReport(report_sxw.rml_parse):
    def __init__(self, cr, uid, name, context):
        super(AccountAssetDepreciationLineReport, self).__init__(cr, uid, name, context)
        self._cr = cr
        self._uid = uid
        self._context = context
        self.localcontext.update({
            'group_by': self.group_by,
            'get_label': self.get_label,
            'label_header': _('Name'),
            'get_depreciation_infos_by_asset_id': self.get_depreciation_infos_by_asset_id,
        })

    @staticmethod
    def check(assets):
        """Call in report_sxw.getObjects method"""
        for asset in assets:
            if asset.state != 'open':
                raise orm.except_orm(_('Error'), _('Please select only assets into service'))
        return assets

    def group_by(self, assets):
        assets_by_group = {}
        for asset in assets:
            group = '%s: %s<span style="position:absolute;left:470px;">%s: %s</span>' % (
                _('Category'), asset.category_id.name,
                _('Currency'), asset.currency_id.symbol
            )
            assets_by_group.setdefault(group, [])
            assets_by_group[group].append(asset)
        return assets_by_group.iteritems()

    def get_label(self, asset):
        return asset.name

    def get_period_stop_date(self, company):
        fiscalyear_start_day = self.pool.get('res.company').get_fiscalyear_start_day(self._cr, self._uid, company.id, self._context)
        return get_period_stop_date(time.strftime('%Y-%m-%d'), fiscalyear_start_day, company.depreciation_period).strftime('%Y-%m-%d')

    def _set_asset_info(self, last_line, asset_info, year, previous_period_stop_date):
        asset_info['%s_period' % last_line.depreciation_type] = last_line.depreciation_value
        asset_info['%s_year' % last_line.depreciation_type] = last_line.current_year_accumulated_value
        asset_info['%s_total' % last_line.depreciation_type] = last_line.accumulated_value
        if last_line.depreciation_date < previous_period_stop_date:
            asset_info['%s_period' % last_line.depreciation_type] = 0.0
            if last_line.year < year:
                asset_info['%s_year' % last_line.depreciation_type] = 0.0
        return asset_info

    def get_depreciation_infos_by_asset_id(self, assets, company):
        res = {}
        year = company.get_fiscalyear()
        period_stop_date = self.get_period_stop_date(company)
        previous_period_stop_date = (datetime.strptime(period_stop_date, '%Y-%m-%d')
                                     - relativedelta(months=company.depreciation_period)).strftime('%Y-%m-%d')
        for asset in assets:
            res[asset.id] = {'accounting_period': 0.0, 'accounting_year': 0.0, 'accounting_total': 0.0,
                             'fiscal_period': 0.0, 'fiscal_year': 0.0, 'fiscal_total': 0.0}
            accounting_lines = [l for l in asset.accounting_depreciation_line_ids if l.is_posted and l.depreciation_date <= period_stop_date]
            if accounting_lines:
                last_line = accounting_lines[-1]
                res[asset.id].update(self._set_asset_info(last_line, res[asset.id], year, previous_period_stop_date))
                fiscal_lines = [l for l in asset.fiscal_depreciation_line_ids if l.is_posted and l.depreciation_date <= period_stop_date]
                if fiscal_lines:
                    last_line = fiscal_lines[-1]
                    res[asset.id].update(self._set_asset_info(last_line, res[asset.id], year, previous_period_stop_date))
        return res


report_sxw.report_sxw('report.account_asset_depreciation_line_report',
                      'account.asset.asset',
                      'smile-addons/smile_account_asset/report/account_asset_depreciation_line_report.mako',
                      parser=AccountAssetDepreciationLineReport)
