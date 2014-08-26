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

from report import report_sxw
from tools.translate import _


class AccountAssetFiscalDeductionReport(report_sxw.rml_parse):
    def __init__(self, cr, uid, name, context):
        super(AccountAssetFiscalDeductionReport, self).__init__(cr, uid, name, context)
        self.localcontext.update({
            'group_by': self.group_by,
            'get_label': self.get_label,
            'label_header': _('Name'),
            'get_depreciation_infos_by_asset_id': self.get_depreciation_infos_by_asset_id,
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

    def get_depreciation_infos_by_asset_id(self, assets, company):
        res = {}
        year = company.get_fiscalyear()
        for asset in assets:
            purchase_value = year_value = accumulated_value = 0.0
            posted_lines = []
            for a in asset.child_ids + [asset]:
                sign = a.asset_type == 'purchase_refund' and -1 or 1
                purchase_value += a.purchase_value * sign
                plines = [l for l in a.accounting_depreciation_line_ids if l.is_posted and l.year <= year]
                posted_lines.extend(plines)
                if plines:
                    last_line = plines[-1]
                    year_value += last_line.year == year and last_line.current_year_accumulated_value * sign or 0.0
                    accumulated_value += last_line.accumulated_value * sign
            book_value = purchase_value - accumulated_value
            non_ded_coeff = purchase_value and \
                ((purchase_value - min(purchase_value, asset.category_id.fiscal_deduction_limit)) / purchase_value) or 0.0
            non_ded_year_value = year_value * non_ded_coeff
            non_ded_accumulated_value = accumulated_value * non_ded_coeff
            res[asset.id] = (year_value, accumulated_value, non_ded_year_value, non_ded_accumulated_value, book_value, purchase_value)
        return res


report_sxw.report_sxw('report.account_asset_fiscal_deduction_report',
                      'account.asset.asset',
                      'smile-addons/smile_account_asset/report/account_asset_fiscal_deduction_report.mako',
                      parser=AccountAssetFiscalDeductionReport)
