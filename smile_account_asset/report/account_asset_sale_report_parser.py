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

from osv import orm
from report import report_sxw
from tools.translate import _


class AccountAssetSaleReport(report_sxw.rml_parse):
    def __init__(self, cr, uid, name, context):
        super(AccountAssetSaleReport, self).__init__(cr, uid, name, context)
        self.localcontext.update({
            'group_by': self.group_by,
            'get_label': self.get_label,
            'label_header': _('Name'),
        })

    @staticmethod
    def check(assets):
        """Call in report_sxw.getObjects method"""
        for asset in assets:
            if asset.state != 'close':
                raise orm.except_orm(_('Error'), _('Please select only disposed assets'))
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


report_sxw.report_sxw('report.account_asset_sale_report',
                      'account.asset.asset',
                      'smile-addons/smile_account_asset/report/account_asset_sale_report.mako',
                      parser=AccountAssetSaleReport)
