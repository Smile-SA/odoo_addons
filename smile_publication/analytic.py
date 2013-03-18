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

import time

from openerp.osv import orm, fields


class AccountAnalyticLine(orm.Model):
    _inherit = 'account.analytic.line'

    def _get_analytic_line_ids_from_accounts(self, cr, uid, ids, context=None):
        return self.pool.get('account.analytic.line').search(cr, uid, [('account_id', 'in', ids)], context=context)

    _columns = {
        'publication_number_id': fields.many2one('publication.number', 'Publication Number'),
        'partner_id': fields.related('account_id', 'partner_id', type='many2one', relation='res.partner', store={
            'account.analytic.line': (lambda self, cr, uid, ids, context=None: ids, ['account_id'], 10),
            'account.analytic.account': (_get_analytic_line_ids_from_accounts, ['partner_id'], 10),
         }, string='Partner'),
    }

    def reverse(self, cr, uid, ids, context=None):
        if isinstance(ids, (int, long)):
            ids = [ids]
        for vals in self.read(cr, uid, ids, context=context, load='_classic_write'):
            del vals['id']
            vals['amount'] *= -1
            vals['invoice_id'] = False
            self.create(cr, uid, vals, context)
        return True

    def unlink(self, cr, uid, ids, context=None):
        if isinstance(ids, (int, long)):
            ids = [ids]
        line_ids_to_delete = []
        line_ids_to_reverse = []
        for line in self.browse(cr, uid, ids, context=None):
            if not line.invoice_id:
                line_ids_to_delete.append(line.id)
            else:
                line_ids_to_reverse.append(line.id)
        self.reverse(cr, uid, line_ids_to_reverse, context)
        return super(AccountAnalyticLine, self).unlink(cr, uid, line_ids_to_delete, context)


class AccountAnalyticAccount(orm.Model):
    _inherit = 'account.analytic.account'

    _columns = {
        'sale_order_line_id': fields.many2one('sale.order.line', 'Sale Order Line', readonly=True),
        'publication_id': fields.many2one('publication.publication', 'Publication', readonly=True),
    }

    def _get_default_invoice_factor_id(self, cr, uid, context=None):
        return self.pool.get('ir.model.data').get_object_reference(cr, uid, 'hr_timesheet_invoice', 'timesheet_invoice_factor1')[1]

    def _get_default_pricelist_id(self, cr, uid, context=None):
        return self.pool.get('ir.model.data').get_object_reference(cr, uid, 'product', 'list0')[1]

    _defaults = {
        'pricelist_id': _get_default_pricelist_id,
        'to_invoice': _get_default_invoice_factor_id,
    }

    def get_account_ids(self, cr, uid, ids, date_stop, context=None):
        date_stop = date_stop or time.strftime('%Y-%m-%d')
        domain = [
            ('date_start', '<=', date_stop),
            '|',
                ('date', '=', False),
                ('date', '>=', date_stop),
        ]
        if ids:
            domain.append(('id', 'in', ids))
        return self.search(cr, uid, domain, context=context)

    def _get_all_publication_numbers(self, cr, uid, accounts, date_stop, context=None):
        publication_ids = [account.publication_id.id for account in accounts if account.publication_id]
        all_publication_number_ids = self.pool.get('publication.publication').get_publication_numbers(cr, uid, publication_ids,
                                                                                                      date_stop=date_stop, context=context)

        return self.pool.get('publication.number').browse(cr, uid, all_publication_number_ids, context)

    def _get_analytic_line_vals(self, cr, uid, account, number, journal_id, context=None):
        product = account.sale_order_line_id.product_id
        return {
            'name': self.pool.get('publication.number').name_get(cr, uid, [number.id], context)[0][1],
            'account_id': account.id,
            'general_account_id': product.property_account_income.id,
            'product_id': product.id,
            'journal_id': journal_id,
            'publication_number_id': number.id,
            'amount': getattr(number.plan_id, 'publisher_price_%s' % product.type_id.format),
            'unit_amount': account.sale_order_line_id.product_uom_qty,
            'to_invoice': account.to_invoice.id,
            # TODO: manage secondary currency
        }

    def generate_publication_lines(self, cr, uid, ids=None, date_stop=None, context=None):
        date_stop = date_stop or time.strftime('%Y-%m-%d')
        ids = self.get_account_ids(cr, uid, ids, date_stop, context)
        accounts = self.browse(cr, uid, ids, context)
        all_publication_numbers = self._get_all_publication_numbers(cr, uid, accounts, date_stop, context)
        journal_id = self.pool.get('account.analytic.journal').search(cr, uid, [('type', '=', 'sale')], limit=1, context=context)[0]
        analytic_line_obj = self.pool.get('account.analytic.line')
        for account in accounts:

            account_publication_number_ids = []
            for line in account.line_ids:
                if not line.publication_number_id:
                    continue
                account_publication_number_ids.append(line.publication_number_id.id)
                if date_stop and line.publication_number_id.publication_date > date_stop:
                    continue
                if line.publication_number_id not in all_publication_numbers:
                    line.unlink()

            for number in all_publication_numbers:
                if number.publication_id != account.publication_id:
                    continue
                if number.publication_date < account.date_start:
                    continue
                if account.date and number.publication_date > account.date:
                    continue
                if number not in account_publication_number_ids:
                    vals = self._get_analytic_line_vals(cr, uid, account, number, journal_id, context)
                    analytic_line_obj.create(cr, uid, vals, context)

        return True
