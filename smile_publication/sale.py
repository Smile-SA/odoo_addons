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

from datetime import datetime
from dateutil.relativedelta import relativedelta

from openerp.osv import orm, fields

from product import OFFER_TYPES


class SaleOrderLine(orm.Model):
    _inherit = "sale.order.line"

    def _get_dates(self, cr, uid, ids, name, arg, context=None):
        res = {}
        for line in self.browse(cr, uid, ids, context):
            if not line.product_id or not line.order_id.date_confirm:
                res[line.id] = {
                    'date_start': False,
                    'date_stop': False,
                }
            elif line.analytic_account_id:
                res[line.id] = {
                    'date_start': line.analytic_account_id.date_start,
                    'date_stop': line.analytic_account_id.date_stop,
                }
            else:
                product = line.product_id
                date_start = datetime.strptime(line.order_id.date_confirm, '%Y-%m-%d') + relativedelta(days=product.delay_start)
                res[line.id] = {'date_start': date_start.strftime('%Y-%m-%d'), 'date_stop': False}
                if product.type_id.offer_type == 'limited':
                    length_type = product.length_type
                    length = product.length
                    if length_type == 'weeks':
                        length_type = 'days'
                        length *= 7
                    date_stop = date_start + relativedelta(**{length_type: length})
                    res[line.id]['date_stop'] = date_stop.strftime('%Y-%m-%d')
        return res

    def _set_date_start(self, cr, uid, line_id, name, value, arg, context=None):
        cr.exeucte('UPDATE sale_order_line SET date_start = %s WHERE id = %s', (value, line_id))
        return True

    def _set_date_stop(self, cr, uid, line_id, name, value, arg, context=None):
        cr.exeucte('UPDATE sale_order_line SET date_stop = %s WHERE id = %s', (value, line_id))
        analytic_account = self.browse(cr, uid, line_id, context).analytic_account_id
        if analytic_account:
            analytic_account.write({'date': value})
        return True

    def _get_line_ids_from_sale_orders(self, cr, uid, ids, context=None):
        res = []
        for order in self.browse(cr, uid, ids, context):
            res.extend([line.id for line in order.order_line])
        return res

    def _get_line_ids_from_analytic_accounts(self, cr, uid, ids, context=None):
        return self.pool.get('sale.order.line').search(cr, uid, [('analytic_account_id', 'in', ids)], context=context)

    def _get_publication(self, cr, uid, ids, name, arg, context=None):
        res = {}
        for line in self.browse(cr, uid, ids, context):
            if not line.product_id:
                res[line.id] = {
                    'publication_id': False,
                    'publication_number_id': False,
                }
            else:
                res[line.id] = {
                    'publication_id': line.product_id.publication_id.id,
                    'publication_number_id': line.product_id.publication_number_id.id,
                }
        return res

    _columns = {
        'analytic_account_id': fields.many2one('account.analytic.account', 'Contract', readonly=True),
        'date_confirm': fields.related('order_id', 'date_confirm', type='date', string='Confirmation Date', readonly=True),
        'date_start': fields.function(_get_dates, fnct_inv=_set_date_start, method=True, type='date', string="Start date", store={
            'sale.order': (_get_line_ids_from_sale_orders, ['state'], 10),
            'account.analytic.account': (_get_line_ids_from_analytic_accounts, ['date_start'], 10),
        }, multi="dates"),
        'date_stop': fields.function(_get_dates, fnct_inv=_set_date_stop, method=True, type='date', string="End date", store={
            'sale.order': (_get_line_ids_from_sale_orders, ['state'], 10),
            'account.analytic.account': (_get_line_ids_from_analytic_accounts, ['date_stop'], 10),
        }, multi="dates"),
        'publication_id': fields.function(_get_publication, method=True, type='many2one', relation='publication.publication', store={
            'sale.order.line': (lambda self, cr, uid, ids, context=None: ids, ['product_id'], 10),
        }, string="Publication", multi="publication"),
        'publication_number_id': fields.function(_get_publication, method=True, type='many2one', relation='publication.number', store={
            'sale.order.line': (lambda self, cr, uid, ids, context=None: ids, ['product_id'], 10),
        }, string="Publication Number", multi="publication"),
        'offer_type': fields.related('product_id', 'type_id', 'offer_type', type='selection', selection=OFFER_TYPES, store={
            'sale.order.line': (lambda self, cr, uid, ids, context=None: ids, ['product_id'], 10),
        }, string='Offer Type', readonly=True),
        'type_id': fields.related('product_id', 'type_id', type='many2one', relation='product.type', store={
            'sale.order.line': (lambda self, cr, uid, ids, context=None: ids, ['product_id'], 10),
        }, string='Product Type', readonly=True),
    }

    def create(self, cr, uid, vals, context=None):
        res_id = super(SaleOrderLine, self).create(cr, uid, vals, context)
        self._store_set_values(cr, uid, [res_id], ['publication_id', 'publication_number_id', 'offer_type', 'type_id'], context)
        return res_id


class SaleOrder(orm.Model):
    _inherit = "sale.order"

    def _get_analytic_account_vals(self, cr, uid, line, context=None):
        return {
            'name': line.name,
            'type': 'contract',
            'partner_id': line.order_id.partner_id.id,
            'date_start': line.date_start,
            'state': 'open',
            'sale_order_line_id': line.id,
            'product_id': line.product_id.id,
            'publication_id': line.product_id.publication_id.id,
        }

    def action_button_confirm(self, cr, uid, ids, context=None):
        assert len(ids) == 1, 'This option should only be used for a single id at a time.'
        res = super(SaleOrder, self).action_button_confirm(cr, uid, ids, context)
        analytic_account_obj = self.pool.get('account.analytic.account')
        for line in self.browse(cr, uid, ids[0], context).order_line:
            if line.product_id and line.product_id.type_id and line.product_id.type_id.offer_type == 'unlimited':
                vals = self._get_analytic_account_vals(cr, uid, line, context)
                line.write({'analytic_account_id': analytic_account_obj.create(cr, uid, vals, context)})
        return res
