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

from osv import orm, fields
from tools.translate import _


class AccountInvoiceLine(orm.Model):
    _inherit = 'account.invoice.line'

    def __init__(self, pool, cr):
        super(AccountInvoiceLine, self).__init__(pool, cr)
        self._unicity_fields = ['asset_category_id', 'company_id', 'currency_id', 'partner_id', 'account_id', 'invoice_line_tax_id']

    _columns = {
        'asset_category_id': fields.many2one('account.asset.category', 'Asset Category', ondelete='restrict'),
        'asset_id': fields.many2one('account.asset.asset', 'Asset', readonly=True, ondelete='restrict'),
        'parent_id': fields.many2one('account.asset.asset', 'Parent Asset', ondelete='restrict'),
        'currency_id': fields.related('invoice_id', 'currency_id', type='many2one', relation='res.currency',
                                      string='Currency', store=True, readonly=True, ondelete='restrict'),
        'date_invoice': fields.related('invoice_id', 'date_invoice', type='date', string='Invoice Date',
                                       store=True, readonly=True),
    }

    def onchange_asset_category_id(self, cr, uid, ids, asset_category_id, company_id, context=None):
        res = {'value': {}}
        if asset_category_id:
            # TODO: add company_id in context of <field name="invoice_line"...> of invoice window action
            asset_category_info = self.pool.get('account.asset.category').read(cr, uid, asset_category_id,
                                                                               ['asset_account_id', 'asset_analytic_account_id'],
                                                                               {'force_company': company_id}, '_classic_write')
            res['value'] = {
                'account_id': asset_category_info['asset_account_id'],
                'account_analytic_id': asset_category_info['asset_analytic_account_id'],
            }
        return res

    def _check_before_creating_asset(self, cr, uid, lines, context=None):
        for field in self._unicity_fields:
            if len(set([str(getattr(line, field)) for line in lines])) > 1:
                field_name = field
                field_obj = self.pool.get('ir.model.fields')
                field_ids = field_obj.search(cr, uid, [('name', '=', field), ('model', '=', self._name)], limit=1, context=context)
                if field_ids:
                    field_name = field_obj.read(cr, uid, field_ids[0], ['field_description'], context)['field_description']
                raise orm.except_orm(_('Error'),
                                     _('You cannot not create an asset from invoice lines with different %s') % field_name)
        for line in lines:
            if line.invoice_id.type == 'in_refund' and not line.parent_id:
                raise orm.except_orm(_('Error'),
                                     _('Please indicate a parent asset in line %s') % line.name)

    def _get_asset_vals(self, cr, uid, lines, context=None):
        line = lines[0]
        amount = sum([l.price_subtotal * (l.invoice_id.journal_id.type == 'purchase_refund' and - 1.0 or 1.0) for l in lines], 0.0)
        quantity = sum([l.quantity * (l.invoice_id.journal_id.type == 'purchase_refund' and - 1.0 or 1.0) for l in lines], 0.0)
        asset_type = 'purchase'
        if amount < 0.0:
            amount = abs(amount)
            quantity = abs(quantity)
            asset_type = 'purchase_refund'
        today = time.strftime('%Y-%m-%m')
        vals = {
            'name': line.name,
            'parent_id': line.parent_id.id,
            'category_id': line.asset_category_id.id,
            'purchase_date': line.invoice_id.date_invoice or today,
            'purchase_account_date': line.invoice_id.date_invoice,
            'purchase_value': amount,
            'quantity': quantity,
            'asset_type': asset_type,
            'supplier_id': line.partner_id.id,
            'company_id': line.company_id.id,
            'currency_id': line.currency_id.id,
            'purchase_tax_ids': [(6, 0, [tax.id for tax in line.invoice_line_tax_id])],
        }
        asset_obj = self.pool.get('account.asset.asset')
        vals.update(asset_obj.onchange_category_id(cr, uid, None, vals['category_id'], context)['value'])
        return vals

    def create_asset(self, cr, uid, ids, context=None):
        context = context or {}
        asset_obj = self.pool.get('account.asset.asset')
        if isinstance(ids, (int, long)):
            ids = [ids]
        lines = [line for line in self.browse(cr, uid, ids, context) if not line.asset_id]
        if not context.get('do_not_check_invoice_lines'):
            self._check_before_creating_asset(cr, uid, lines, context)
        if not lines:
            raise orm.except_orm(_('Error'), _('No asset to create from these invoice lines!'))
        vals = self._get_asset_vals(cr, uid, lines, context)
        asset_id = asset_obj.create(cr, uid, vals, context)
        self.write(cr, uid, [l.id for l in lines], {'asset_id': asset_id}, context)
        if lines[0].asset_category_id.confirm_asset:
            asset_obj.confirm_asset_purchase(cr, uid, [asset_id], context)
        return asset_id

    def _group_by_asset(self, cr, uid, ids, context=None):
        res = {}
        if isinstance(ids, (int, long)):
            ids = [ids]
        for line in self.browse(cr, uid, ids, context):
            if line.asset_category_id and line.invoice_id.journal_id.type in ('purchase', 'purchase_refund'):
                group_key = [getattr(line, field) for field in self._unicity_fields]
                res.setdefault(str(group_key), []).append(line.id)
        return res.values()

    def create_assets(self, cr, uid, ids, context=None):
        context_copy = context and context.copy() or {}
        context_copy['do_not_check_invoice_lines'] = True
        lines_by_asset = self._group_by_asset(cr, uid, ids, context)
        for line_ids in lines_by_asset:
            self.create_asset(cr, uid, line_ids, context_copy)
        return True

    def _update_vals(self, cr, uid, vals, context=None):
        vals = vals or {}
        if ('account_id' not in vals or 'analytic_account_id' not in vals) and vals.get('asset_category_id'):
            asset_category_info = self.pool.get('account.asset.category').read(cr, uid, vals['asset_category_id'],
                                                                               ['asset_account_id', 'asset_analytic_account_id'],
                                                                               context, '_classic_write')
            if 'account_id' not in vals:
                vals['account_id'] = asset_category_info['asset_account_id']
                if isinstance(vals['account_id'], tuple):  # INFO: bug with load params in read method
                    vals['account_id'] = vals['account_id'][0]
            if 'analytic_account_id' not in vals:
                vals['account_analytic_id'] = asset_category_info['asset_analytic_account_id']
                if isinstance(vals['account_analytic_id'], tuple):
                    vals['account_analytic_id'] = vals['account_analytic_id'][0]
        return vals

    def create(self, cr, uid, vals, context=None):
        vals = self._update_vals(cr, uid, vals, context)
        return super(AccountInvoiceLine, self).create(cr, uid, vals, context)

    def write(self, cr, uid, ids, vals, context=None):
        vals = self._update_vals(cr, uid, vals, context)
        return super(AccountInvoiceLine, self).write(cr, uid, ids, vals, context)

    def copy_data(self, cr, uid, invoice_line_id, default=None, context=None):
        default = default or {}
        default['asset_id'] = False
        return super(AccountInvoiceLine, self).copy_data(cr, uid, invoice_line_id, default, context=context)

    def move_line_get_item(self, cr, uid, line, context=None):
        res = super(AccountInvoiceLine, self).move_line_get_item(cr, uid, line, context)
        res['asset_id'] = line.asset_id.id
        return res


class AccountInvoice(orm.Model):
    _inherit = 'account.invoice'

    def action_move_create(self, cr, uid, ids, context=None):
        if isinstance(ids, (int, long)):
            ids = [ids]
        line_ids = []
        for invoice in self.browse(cr, uid, ids, context):
            for line in invoice.invoice_line:
                if line.asset_category_id and line.asset_category_id.asset_creation == 'auto':
                    line_ids.append(line.id)
        self.pool.get('account.invoice.line').create_assets(cr, uid, line_ids, context)
        return super(AccountInvoice, self).action_move_create(cr, uid, ids, context)

    def line_get_convert(self, cr, uid, invoice_line_info, partner_id, date, context=None):
        res = super(AccountInvoice, self).line_get_convert(cr, uid, invoice_line_info, partner_id, date, context)
        res['asset_id'] = invoice_line_info.get('asset_id', False)
        return res

    def copy_data(self, cr, uid, id_, default=None, context=None):
        default = default or {}
        default['rg_voucher_line'] = []
        return super(AccountInvoice, self).copy_data(cr, uid, id_, default, context)
