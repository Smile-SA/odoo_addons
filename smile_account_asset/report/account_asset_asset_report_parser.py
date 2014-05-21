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

from report import report_sxw
from tools.translate import _

from openerp.addons.smile_account_asset.account_asset_tools import get_period_stop_date


class AccountAssetAssetReport(report_sxw.rml_parse):
    def __init__(self, cr, uid, name, context):
        super(AccountAssetAssetReport, self).__init__(cr, uid, name, context)
        self._cr = cr
        self._uid = uid
        self._context = context
        self.localcontext.update({
            'group_by': self.group_by,
            'get_label': self.get_label,
            'label_header': _('Name'),
            'get_depreciation_infos_by_asset_id': self.get_depreciation_infos_by_asset_id,
            'get_value_selection': self.get_value_selection,
        })

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
        return get_period_stop_date(time.strftime('%Y-%m-%d'), fiscalyear_start_day, company.depreciation_period)

    def get_depreciation_infos_by_asset_id(self, assets, company):
        res = {}
        year = company.get_fiscalyear()
        for asset in assets:
            start_value = current_value = end_value = 0.0
            date_start = ''
            posted_lines = [l for l in asset.accounting_depreciation_line_ids if l.is_posted and l.year <= year]
            if posted_lines:
                last_line = posted_lines[-1]
                first_line = posted_lines[0]
                date_start = first_line.depreciation_date
                start_value = last_line.previous_years_accumulated_value
                current_value = last_line.current_year_accumulated_value
                if last_line.year < year:
                    start_value += current_value
                    current_value = 0.0
                end_value = start_value + current_value
            book_value = asset.purchase_value - end_value
            res[asset.id] = (start_value, current_value, end_value, book_value, date_start)
        return res

    def get_value_selection(self,  model, value, field, context):
        selection = self.pool.get(model).fields_get(self.cr, self.uid, [field], context=context)[field]['selection']
        for key, v in selection:
            if key == value:
                return v
        return value


report_sxw.report_sxw('report.account_asset_asset_report',
                      'account.asset.asset',
                      'smile-addons/smile_account_asset/report/account_asset_asset_report.mako',
                      parser=AccountAssetAssetReport)
