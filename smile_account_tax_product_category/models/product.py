# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2015 Smile (<http://www.smile.fr>).
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

from openerp import api, fields, models


class ProductCategory(models.Model):
    _inherit = 'product.category'
    _parent_store = False

    @api.one
    def _get_total_taxes(self):
        categ = self
        customer_taxes = categ.taxes_id
        supplier_taxes = categ.supplier_taxes_id
        while categ.parent_id and (not customer_taxes or not supplier_taxes):
            categ = categ.parent_id
            if not customer_taxes:
                customer_taxes |= categ.taxes_id
            if not supplier_taxes:
                supplier_taxes |= categ.supplier_taxes_id
        self.total_taxes_id = customer_taxes
        self.total_supplier_taxes_id = supplier_taxes

    taxes_id = fields.Many2many('account.tax', 'product_category_taxes_rel', 'categ_id', 'tax_id', 'Customer Taxes',
                                domain=[('parent_id', '=', False), ('type_tax_use', 'in', ['sale', 'all'])],
                                help="Taxes change in product category is not propagated in existing products")
    supplier_taxes_id = fields.Many2many('account.tax', 'product_category_supplier_taxes_rel', 'categ_id', 'tax_id', 'Supplier Taxes',
                                         domain=[('parent_id', '=', False), ('type_tax_use', 'in', ['purchase', 'all'])],
                                         help="Taxes change in product category is not propagated in existing products")
    total_taxes_id = fields.Many2many('account.tax', string='Inherited Customer Taxes', compute='_get_total_taxes')
    total_supplier_taxes_id = fields.Many2many('account.tax', string='Inherited Supplier Taxes', compute='_get_total_taxes')

    @api.multi
    def write(self, vals):
        old_taxes_to_keep = {}
        company = self.env.user.company_id
        for field in ('taxes_id', 'supplier_taxes_id'):
            if field in vals:
                for categ in self.sudo():
                    old_taxes_to_keep.setdefault(field, {})
                    old_taxes_to_keep[field][categ] = getattr(categ, field).filtered(lambda tax: tax.company_id != company)
        res = super(ProductCategory, self).write(vals)
        for field in old_taxes_to_keep:
            for categ in old_taxes_to_keep[field]:
                taxes = getattr(categ, field)
                taxes |= old_taxes_to_keep[field][categ]
        return res


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    @api.onchange('categ_id')
    def _onchange_categ_id(self):
        if self.categ_id:
            self.taxes_id = self.categ_id.total_taxes_id
            self.supplier_taxes_id = self.categ_id.total_supplier_taxes_id

    @api.model
    def create(self, vals):
        product_tmpl = super(ProductTemplate, self).create(vals)
        if vals.get('categ_id') and 'taxes_id' not in vals and 'supplier_taxes_id' not in vals:
            product_tmpl._onchange_categ_id()
        return product_tmpl


class ProductProduct(models.Model):
    _inherit = 'product.product'

    @api.onchange('categ_id')
    def _onchange_categ_id(self):
        self.product_tmpl_id._onchange_categ_id()
