# -*- encoding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2014 Smile (<http://www.smile.fr>). All Rights Reserved
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

from openerp import api, fields, models


class ProductCategory(models.Model):
    _inherit = 'product.category'

    @api.onchange('asset_category_id')
    def onchange_asset_category(self):
        if self.asset_category_id:
            self.property_account_expense_categ = self.asset_category_id.asset_account_id
            self.property_account_income_categ = self.asset_category_id.sale_receivable_account_id

    asset_category_id = fields.Many2one('account.asset.category', 'Asset Category', company_dependent=True)


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    @api.onchange('asset_category_id')
    def onchange_asset_category(self):
        if self.asset_category_id:
            self.property_account_expense = self.asset_category_id.asset_account_id
            self.property_account_income = self.asset_category_id.sale_receivable_account_id

    asset_category_id = fields.Many2one('account.asset.category', 'Asset Category', company_dependent=True)
