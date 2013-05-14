# -*- encoding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2013 Smile (<http://www.smile.fr>). All Rights Reserved
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

from openerp.osv import orm, fields


class ProductType(orm.Model):
    _name = "product.type"
    _description = "Product Type"

    _columns = {
        'name': fields.char('Name', size=64, required=True),
        'active': fields.boolean('Active'),
        'company_id': fields.many2one('res.company', 'Company', select=True),

        'type': fields.selection([('product', 'Stockable Product'), ('consu', 'Consumable'), ('service', 'Service')],
                                 'Product Type', required=True),
        'procure_method': fields.selection([('make_to_stock', 'Make to Stock'), ('make_to_order', 'Make to Order')],
                                           'Procurement Method', required=True),
        'supply_method': fields.selection([('produce', 'Manufacture'), ('buy', 'Buy')], 'Supply Method', required=True),

        'taxes_id': fields.many2many('account.tax', 'product_type_taxes_rel', 'prod_id', 'tax_id', 'Customer Taxes',
            domain=[('parent_id', '=', False), ('type_tax_use', 'in', ['sale', 'all'])]),
        'supplier_taxes_id': fields.many2many('account.tax', 'product_type_supplier_taxes_rel', 'prod_id', 'tax_id',
            'Supplier Taxes', domain=[('parent_id', '=', False), ('type_tax_use', 'in', ['purchase', 'all'])]),
        'property_account_income': fields.property('account.account', type='many2one', relation='account.account',
            string="Income Account", view_load=True,
            help="This account will be used for invoices instead of the default one to value sales for the current product."),
        'property_account_expense': fields.property('account.account', type='many2one', relation='account.account',
            string="Expense Account", view_load=True,
            help="This account will be used for invoices instead of the default one to value expenses for the current product."),
    }

    def _get_default_company_id(self, cr, uid, context=None):
        return self.pool.get('res.company')._company_default_get(cr, uid, self._name, context=context)

    _defaults = {
        'active': True,
        'company_id': _get_default_company_id,
    }

    _sql_constraints = [
        ('uniq_name', 'UNIQUE(name)', 'Product Type must be unique'),
    ]


class ProductProduct(orm.Model):
    _inherit = 'product.product'

    _columns = {
        'type_id': fields.many2one('product.type', 'Product Type', required=False, ondelete="restrict"),
    }

    def onchange_product_type(self, cr, uid, ids, type_id, context=None):
        res = {'value': {}}
        if type_id:
            product_type = self.pool.get('product.type').browse(cr, uid, type_id, context)
            res['value'] = {
                'type': product_type.type,
                'procure_method': product_type.procure_method,
                'supply_method': product_type.supply_method,
                'taxes_id': [tax.id for tax in product_type.taxes_id],
                'supplier_taxes_id': [tax.id for tax in product_type.supplier_taxes_id],
                'property_account_income': product_type.property_account_income.id,
                'property_account_expense': product_type.property_account_expense.id,
            }
        return res

    def _update_vals(self, cr, uid, vals, context=None):
        if vals.get('type_id'):
            vals.update(self.onchange_product_type(cr, uid, None, vals['type_id'], context)['value'])
        return vals

    def create(self, cr, uid, vals, context=None):
        vals = self._update_vals(cr, uid, vals, context)
        return super(ProductProduct, self).create(cr, uid, vals, context)

    def write(self, cr, uid, ids, vals, context=None):
        vals = self._update_vals(cr, uid, vals, context)
        return super(ProductProduct, self).write(cr, uid, ids, vals, context)
