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

from openerp import SUPERUSER_ID
import openerp.addons.decimal_precision as dp
from openerp.osv import orm, fields
from openerp import tools
from openerp.tools.translate import _

PRODUCT_FORMATS = [('paper', 'Paper'), ('digital', 'Digital')]
OFFER_TYPES = [('limited', 'Limited'), ('unlimited', 'Unlimited')]


class ProductType(orm.Model):
    _name = "product.type"
    _description = "Product Type"

    _columns = {
        'name': fields.char('Name', size=64, required=True),
        'active': fields.boolean('Active'),

        'type': fields.selection([('product', 'Stockable Product'), ('consu', 'Consumable'), ('service', 'Service')],
                                 'Product Type', required=True),
        'procure_method': fields.selection([('make_to_stock', 'Make to Stock'), ('make_to_order', 'Make to Order')],
                                           'Procurement Method', required=True),
        'supply_method': fields.selection([('produce', 'Manufacture'), ('buy', 'Buy')], 'Supply Method', required=True),
        'sale_shop_ids': fields.many2many('sale.shop', 'sale_shop_publication_rel', 'publication_id', 'shop_id', 'Shops',
                                          help="If empty, this publication is available in all shops"),

        'format': fields.selection(PRODUCT_FORMATS, 'Format', required=True),
        'must_be_linked_to_publication': fields.boolean('Must be linked to publication'),
        'must_be_linked_to_publication_number': fields.boolean('Must be linked to publication number'),
        'can_be_sold_beyond_publication_period': fields.boolean('Can be sold beyond publication period'),
        'delay_start': fields.integer('Delay of starting (in days)'),
        'invoicing_mode': fields.selection([('pre', 'Pre-invoicing'), ('post', 'Post-invoicing')], 'Invoicing Mode', required=True),
        'offer_type': fields.selection(OFFER_TYPES, 'Offer type', required=True),

        'company_id': fields.many2one('res.company', 'Company', select=True),

        'client_action_id': fields.many2one('ir.values', 'Client Action'),
        'client_action_server_id': fields.many2one('ir.actions.server', 'Client Action Server', readonly=True),

        'taxes_id': fields.many2many('account.tax', 'product_type_taxes_rel', 'prod_id', 'tax_id', 'Customer Taxes',
            domain=[('parent_id', '=', False), ('type_tax_use', 'in', ['sale', 'all'])]),
        'supplier_taxes_id': fields.many2many('account.tax', 'product_type_supplier_taxes_rel', 'prod_id', 'tax_id',
            'Supplier Taxes', domain=[('parent_id', '=', False), ('type_tax_use', 'in', ['purchase', 'all'])]),
        'property_account_income': fields.property(
            'account.account',
            type='many2one',
            relation='account.account',
            string="Income Account",
            view_load=True,
            help="This account will be used for invoices instead of the default one to value sales for the current product."),
        'property_account_expense': fields.property(
            'account.account',
            type='many2one',
            relation='account.account',
            string="Expense Account",
            view_load=True,
            help="This account will be used for invoices instead of the default one to value expenses for the current product."),
    }

    def _get_default_company_id(self, cr, uid, context=None):
        return self.pool.get('res.company')._company_default_get(cr, uid, self._name, context=context)

    _defaults = {
        'active': True,
        'delay_start': 1,
        'company_id': _get_default_company_id,
    }

    _sql_constraints = [
        ('uniq_name', 'UNIQUE(name)', 'Product Type must be unique'),
    ]

    def _get_server_action_vals(self, cr, uid, product_type, model_id, context=None):
        return {
            'name': _('Generate %s') % product_type.name,
            'model_id': model_id,
            'state': 'code',
            'code': """context['publication_number_ids'] = context.get('active_ids', [])
self.pool.get('product.type').generate_products(cr, uid, %d, context)""" % (product_type.id,),
        }

    def _get_client_action_vals(self, cr, uid, product_type, model_id, server_action_id, context=None):
        return {
            'name': product_type.name,
            'object': True,
            'model_id': model_id,
            'model': 'publication.number',
            'key2': 'client_action_multi',
            'value': 'ir.actions.server,%d' % server_action_id,
        }

    def create_client_action(self, cr, uid, ids, context=None):
        if isinstance(ids, (int, long)):
            ids = [ids]
        model_id = self.pool.get('ir.model.data').get_object_reference(cr, SUPERUSER_ID, 'smile_publication', 'model_publication_number')[1]
        for product_type in self.browse(cr, uid, ids, context):
            if not product_type.client_action_id:
                vals = self._get_server_action_vals(cr, uid, product_type, model_id, context)
                server_action_id = self.pool.get('ir.actions.server').create(cr, SUPERUSER_ID, vals, context)
                vals2 = self._get_client_action_vals(cr, uid, product_type, model_id, server_action_id, context)
                client_action_id = self.pool.get('ir.values').create(cr, SUPERUSER_ID, vals2, context)
                product_type.write({'client_action_id': client_action_id, 'client_action_server_id': server_action_id})
        return True

    def _check_client_action(self, cr, uid, ids, vals, context=None):
        if isinstance(ids, (int, long)):
            ids = [ids]
        if 'must_be_linked_to_publication_number' in vals:
            if vals['must_be_linked_to_publication_number']:
                self.create_client_action(cr, uid, ids, context)
            else:
                for product_type in self.browse(cr, SUPERUSER_ID, ids, context):
                    if product_type.client_action_id:
                        product_type.client_action_id.unlink()
                        product_type.client_action_server_id.unlink()
        return True

    def create(self, cr, uid, vals, context=None):
        res_id = super(ProductType, self).create(cr, uid, vals, context)
        self._check_client_action(cr, uid, res_id, vals, context)
        return res_id

    def write(self, cr, uid, ids, vals, context=None):
        self._check_client_action(cr, uid, ids, vals, context)
        return super(ProductType, self).write(cr, uid, ids, vals, context)

    def _get_product_vals(self, cr, uid, product_type, number, publisher_price, purchase_price, context=None):
        return {
            'name': '%s %s - %s' % (number.publication_id.name, number.number, product_type.name),
            'type_id': product_type.id,
            'publication_id': number.publication_id.id,
            'publication_number_id': number.id,
            'list_price': publisher_price,
            'standard_price': purchase_price,
            'seller_ids': [(0, 0, {
                'name': number.publication_id.publisher_id.id,
                'min_qty': 0.0,
                'pricelist_ids': [(0, 0, {
                    'min_quantity': 0.0,
                    'price': purchase_price,
                })],
            })],
        }

    def generate_products(self, cr, uid, ids, context=None):
        context = context or {}
        if not context.get('publication_number_ids'):
            return False
        if isinstance(ids, (int, long)):
            ids = [ids]
        product_obj = self.pool.get('product.product')
        number_obj = self.pool.get('publication.number')
        for product_type in self.browse(cr, uid, ids, context):
            for number in number_obj.browse(cr, uid, context['publication_number_ids'], context):
                purchase_price = 0.0
                publisher_price = getattr(number.plan_id, 'publisher_price_' + product_type.format)
                if product_type.offer_type == 'limited':
                    purchase_price = publisher_price * getattr(number.plan_id, 'commission_rate_' + product_type.format) / 100.0
                vals = self._get_product_vals(cr, uid, product_type, number, publisher_price, purchase_price, context)
                product_obj.create(cr, uid, vals, context)
        return True


class ProductProduct(orm.Model):
    _inherit = 'product.product'

    def _get_sale_shops(self, cr, uid, ids, name, arg, context=None):
        res = {}
        for product in self.browse(cr, uid, ids, context):
            res[product.id] = []
            if product.publication_id:
                res[product.id].extend([shop.id for shop in product.publication_id.sale_shop_ids])
            if product.type_id:
                res[product.id].extend([shop.id for shop in product.type_id.sale_shop_ids])
            res[product.id] = list(set(res[product.id]))
        return res

    def _search_sale_shops(self, cr, uid, ids, name, value, args, context=None):
        if not args:
            return []
        for cond in args[:]:
            if cond[0] != name:  # Remote field not managed
                continue
            args.remove(cond)
            cond[0] = 'type_id.sale_shop_ids'
            args.append(cond)
            cond[0] = 'publication_id.sale_shop_ids'
            args.append(cond)
        return args

    def _get_prices(self, cr, uid, ids, name, arg, context=None):
        res = {}
        for product in self.browse(cr, uid, ids, context):
            res[product.id] = {
                'commission_rate': 0.0,
                'stand_price': 0.0,
                'publisher_price': product.list_price,
            }
            if product.publication_number_id:
                res[product.id] = {
                    'commission_rate': getattr(product.publication_number_id.plan_id, 'commission_rate_%s' % product.type_id.format),
                    'stand_price': getattr(product.publication_number_id.plan_id, 'stand_price_%s' % product.type_id.format),
                    'publisher_price': getattr(product.publication_number_id.plan_id, 'publisher_price_%s' % product.type_id.format),
                }
        return res

    def _set_commission_rate(self, cr, uid, product_id, name, value, arg, context=None):
        product = self.browse(cr, uid, product_id, context)
        if product.type_id.must_be_linked_to_publication_number:
            raise orm.except_orm(_('Error'), _('You cannot change commission rate for this type for product'))
        cr.execute('UPDATE product_product SET commission_rate = %s WHERE id = %s', (value, product_id))
        return True

    def _set_stand_price(self, cr, uid, product_id, name, value, arg, context=None):
        product = self.browse(cr, uid, product_id, context)
        if product.type_id.must_be_linked_to_publication_number:
            raise orm.except_orm(_('Error'), _('You cannot change stand price for this type for product'))
        cr.execute('UPDATE product_product SET stand_price = %s WHERE id = %s', (value, product_id))
        return True

    def _set_publisher_price(self, cr, uid, product_id, name, value, arg, context=None):
        product = self.browse(cr, uid, product_id, context)
        if product.type_id.must_be_linked_to_publication_number:
            raise orm.except_orm(_('Error'), _('You cannot change stand price for this type for product'))
        self.write(cr, uid, product_id, {'list_price': value}, context)
        cr.execute('UPDATE product_product SET publisher_price=%s WHERE id=%s', (value, product_id))
        return True

    def _get_image(self, cr, uid, ids, name, args, context=None):
        result = dict.fromkeys(ids, False)
        for product in self.browse(cr, uid, ids, context):
            if product.publication_number_id:
                result[product.id] = {'image_small': product.publication_number_id.image_small}
            if not result[product.id] and product.publication_id:
                result[product.id] = {'image_small': product.publication_id.image_small}
            if not result[product.id]:
                result[product.id] = tools.image_get_resized_images(product.image, avoid_resize_medium=True)
        return result

    def _set_image(self, cr, uid, id, name, value, args, context=None):
        return self.write(cr, uid, [id], {'image': tools.image_resize_image_big(value)}, context=context)

    _columns = {
        'active': fields.boolean('Active'),
        'publication_id': fields.many2one('publication.publication', 'Publication', required=False, ondelete="restrict"),
        'type_id': fields.many2one('product.type', 'Offer Type', required=False, ondelete="restrict"),
        'format': fields.related('type_id', 'format', type='selection', relation=PRODUCT_FORMATS, string='Format', readonly=True),
        'sale_shop_ids': fields.function(_get_sale_shops, fnct_search=_search_sale_shops, method=True,
                                         type='many2many', relation='sale.shop', string='Shops'),
        'publication_number_id': fields.many2one('publication.number', 'Publication Number', required=False, ondelete="cascade"),
        'commission_rate': fields.function(_get_prices, fnct_inv=_set_commission_rate, method=True, multi="publication_prices", store={
                                                'product.product': (lambda self, cr, uid, ids, context=None: ids, ['publication_number_id'], 10),
                                           }, type='float', digits_compute=dp.get_precision('Product Price'), string="Commission Rate"),
        'stand_price': fields.function(_get_prices, fnct_inv=_set_stand_price, method=True, multi="publication_prices", store={
                                            'product.product': (lambda self, cr, uid, ids, context=None: ids, ['publication_number_id'], 10),
                                       }, type='float', digits_compute=dp.get_precision('Product Price'), string="Stand Price"),
        'publisher_price': fields.function(_get_prices, fnct_inv=_set_publisher_price, method=True, multi="publication_prices", store={
                                                'product.product': (lambda self, cr, uid, ids, context=None: ids,
                                                                     ['list_price', 'publication_number_id'], 10),
                                           }, type='float', digits_compute=dp.get_precision('Product Price'), string="Publisher Price"),
        'offer_type': fields.related('type_id', 'offer_type', type='selection', selection=OFFER_TYPES, string='Offer Type', readonly=True),
        'must_be_linked_to_publication': fields.related('type_id', 'must_be_linked_to_publication',
                                                        type='boolean', string='Must be linked to publication', readonly=True),
        'must_be_linked_to_publication_number': fields.related('type_id', 'must_be_linked_to_publication_number',
                                                               type='boolean', string='Must be linked to publication number', readonly=True),
        'delay_start': fields.integer('Delay of starting (in days)'),
        'length': fields.integer('Length'),
        'length_type': fields.selection([
            ('days', 'Days'),
            ('weeks', 'Weeks'),
            ('months', 'Months'),
            ('years', 'Years'),
        ]),
        'numbers': fields.integer('Publication numbers'),

        'image_small': fields.function(_get_image, fnct_inv=_set_image,
            string="Small-sized image", type="binary", multi="_get_image",
            store={
                'product.product': (lambda self, cr, uid, ids, c={}: ids, ['image', 'publication_id', 'publication_number_id'], 10),
            },
            help="Small-sized image of the product. It is automatically "
                 "resized as a 64x64px image, with aspect ratio preserved. "
                 "Use this field anywhere a small image is required."),
        'analytic_line_ids': fields.one2many('account.analytic.line', 'product_id', 'Analytic Lines'),
    }

    _defaults = {
        'active': True,
        'delay_start': 7,
        'length_type': 'years',
        'numbers': 1,
    }

    def _check_commission_rate(self, cr, uid, ids, context=None):
        if isinstance(ids, (int, long)):
            ids = [ids]
        for product in self.browse(cr, uid, ids, context):
            if product.commission_rate < 0.0 or product.commission_rate > 100.0:
                return False
        return True

    _constraints = [
        (_check_commission_rate, 'Commission Rate must be between 0.0 and 100.0', ['commission_rate']),
    ]

    def copy_data(self, cr, uid, product_id, default=None, context=None):
        default = default or {}
        default['analytic_line_ids'] = []
        return super(ProductProduct, self).copy_data(cr, uid, product_id, default, context)

    def onchange_product_type(self, cr, uid, ids, type_id, context=None):
        res = {'value': {}}
        if type_id:
            product_type = self.pool.get('product.type').browse(cr, uid, type_id, context)
            res['value'] = {
                'type': product_type.type,
                'procure_method': product_type.procure_method,
                'supply_method': product_type.supply_method,
                'offer_type': product_type.offer_type,
                'must_be_linked_to_publication': product_type.must_be_linked_to_publication,
                'must_be_linked_to_publication_number': product_type.must_be_linked_to_publication_number,
                'delay_start': product_type.delay_start,
                'taxes_id': [tax.id for tax in product_type.taxes_id],
                'supplier_taxes_id': [tax.id for tax in product_type.supplier_taxes_id],
                'property_account_income': product_type.property_account_income.id,
                'property_account_expense': product_type.property_account_expense.id,
            }
        return res

    def _check_change(self, cr, uid, vals, context=None):
        for field in ('publication_id', 'publisher_price', 'commission_rate'):
            if field in vals:
                return True
        return False

    def _update_seller_infos(self, cr, uid, ids, vals, context=None):
        if isinstance(ids, (int, long)):
            ids = [ids]
        supplierinfo_obj = self.pool.get('product.supplierinfo')
        if self._check_change(cr, uid, vals, context):
            for product in self.browse(cr, uid, ids, context):
                if product.publication_id and not product.type_id.must_be_linked_to_publication_number:
                    supplierinfo_obj.unlink(cr, uid, [seller.id for seller in product.seller_ids], context)
                    price = product.type_id.offer_type == 'unlimited' and product.publisher_price * product.commission_rate / 100.0 or 0.0
                    supplierinfo_obj.create(cr, uid,                 {
                        'name': product.publication_id.publisher_id.id,
                        'product_id': product.id,
                        'min_qty': 0.0,
                        'pricelist_ids': [(0, 0, {
                            'min_quantity': 0.0,
                            'price': price,
                        })],
                    }, context)
                    product.write({'standard_price': price})
        return True

    def _update_vals(self, cr, uid, vals, context=None):
        if vals.get('type_id'):
            vals.update(self.onchange_product_type(cr, uid, None, vals['type_id'], context)['value'])
        return vals

    def create(self, cr, uid, vals, context=None):
        vals = self._update_vals(cr, uid, vals, context)
        res_id = super(ProductProduct, self).create(cr, uid, vals, context)
        self._update_seller_infos(cr, uid, res_id, vals, context)
        return res_id

    def write(self, cr, uid, ids, vals, context=None):
        vals = self._update_vals(cr, uid, vals, context)
        res = super(ProductProduct, self).write(cr, uid, ids, vals, context)
        self._update_seller_infos(cr, uid, ids, vals, context)
        return res
