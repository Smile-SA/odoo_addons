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

from openerp import api, fields, models, _
from openerp.exceptions import Warning


class AccountInvoiceLine(models.Model):
    _inherit = 'account.invoice.line'
    _unicity_fields = ['asset_category_id', 'company_id', 'currency_id', 'partner_id', 'account_id', 'invoice_line_tax_id']

    asset_category_id = fields.Many2one('account.asset.category', 'Asset Category', ondelete='restrict')
    asset_id = fields.Many2one('account.asset.asset', 'Asset', readonly=True, ondelete='restrict', copyable=False)
    parent_id = fields.Many2one('account.asset.asset', 'Parent Asset', ondelete='restrict')
    currency_id = fields.Many2one('res.currency', 'Currency', related='invoice_id.currency_id', readonly=True, ondelete='restrict')
    date_invoice = fields.Date('Invoice Date', related='invoice_id.date_invoice', readonly=True)
    note = fields.Text()

    @api.multi
    def product_id_change(self, product_id, uom_id, qty=0, name='', type='out_invoice',
                          partner_id=False, fposition_id=False, price_unit=False, currency_id=False,
                          context=None, company_id=None):
        res = super(AccountInvoiceLine, self).product_id_change(product_id, uom_id, qty, name, type,
                                                                partner_id, fposition_id, price_unit,
                                                                currency_id, context, company_id)
        res.setdefault('value', {})
        if product_id:
            product = self.env['product.product'].browse(product_id)
            if product.asset_category_id:
                res['value']['asset_category_id'] = product.asset_category_id.id
            elif product.categ_id.asset_category_id:
                res['value']['asset_category_id'] = product.categ_id.asset_category_id.id
        return res

    @api.onchange("asset_category_id")
    def onchange_asset_category(self):
        if self.asset_category_id:
            self.account_id = self.asset_category_id.asset_account_id.id
            self.account_analytic_id = self.asset_category_id.asset_analytic_account_id.id

    @api.multi
    def _check_before_creating_asset(self):
        for fname in AccountInvoiceLine._unicity_fields:
            if len(set([str(getattr(line, fname)) for line in self])) > 1:
                field_name = fname
                field = self.env['ir.model.fields'].search([('name', '=', fname), ('model', '=', self._name)], limit=1)
                if field:
                    field_name = field.field_description
                raise Warning(_('You cannot not create an asset from invoice lines with different %s') % field_name)
        for line in self:
            if line.invoice_id.type == 'in_refund' and not line.parent_id:
                raise Warning(_('Please indicate a parent asset in line %s') % line.name)

    @api.multi
    def _get_asset_vals(self):
        line = self[0]
        coeff = lambda l: l.invoice_id.journal_id.type == 'purchase_refund' and -1 or 1
        amount = sum([l.price_subtotal * coeff(l) for l in self])
        quantity = sum([l.quantity * coeff(l) for l in self])
        asset_type = 'purchase'
        if amount < 0.0:
            amount = abs(amount)
            quantity = abs(quantity)
            asset_type = 'purchase_refund'
        vals = {
            'name': line.name,
            'parent_id': line.parent_id.id,
            'category_id': line.asset_category_id.id,
            'purchase_date': line.invoice_id.date_invoice or fields.Date.today(),
            'purchase_account_date': line.invoice_id.date_invoice,
            'purchase_value': amount,
            'quantity': quantity,
            'asset_type': asset_type,
            'supplier_id': line.partner_id.id,
            'company_id': line.company_id.id,
            'currency_id': line.currency_id.id,
            'purchase_tax_ids': [(6, 0, [tax.id for tax in line.invoice_line_tax_id])],
        }
        vals.update(self.pool['account.asset.asset'].onchange_category_id(self._cr, self._uid, None,
                                                                          vals['category_id'],
                                                                          self._context)['value'])
        return vals

    @api.multi
    @api.returns('account.asset.asset', lambda value: value.id)
    def create_asset(self):
        asset_obj = self.env['account.asset.asset']
        lines = self.filtered(lambda line: not line.asset_id)
        if not self._context.get('do_not_check_invoice_lines'):
            self._check_before_creating_asset()
        if not lines:
            raise Warning(_('No asset to create from these invoice lines!'))
        vals = lines._get_asset_vals()
        asset = asset_obj.create(vals)
        self.write({'asset_id': asset.id})
        if lines[0].asset_category_id.confirm_asset:
            asset.confirm_asset_purchase()
        return asset

    @api.multi
    def _group_by_asset(self):
        res = {}
        for line in self:
            if line.asset_category_id and line.invoice_id.journal_id.type in ('purchase', 'purchase_refund'):
                group_key = [getattr(line, field) for field in self._unicity_fields]
                res.setdefault(str(group_key), []).append(line.id)
        return res.values()

    @api.multi
    def create_assets(self):
        for line_ids in self._group_by_asset():
            self.with_context(do_not_check_invoice_lines=True).browse(line_ids).create_asset()
        return True

    @api.model
    def _update_vals(self, vals):
        vals = vals or {}
        if ('account_id' not in vals or 'analytic_account_id' not in vals) and vals.get('asset_category_id'):
            asset_category = self.env['account.asset.category'].browse(vals['asset_category_id'])
            if 'account_id' not in vals:
                vals['account_id'] = asset_category.asset_account_id.id
            if 'analytic_account_id' not in vals:
                vals['account_analytic_id'] = asset_category.asset_analytic_account_id.id
        return vals

    @api.model
    @api.returns('self', lambda value: value.id)
    def create(self, vals):
        vals = self._update_vals(vals)
        return super(AccountInvoiceLine, self).create(vals)

    @api.multi
    def write(self, vals):
        vals = self._update_vals(vals)
        return super(AccountInvoiceLine, self).write(vals)

    @api.model
    def move_line_get_item(self, line):
        res = super(AccountInvoiceLine, self).move_line_get_item(line)
        res['asset_id'] = line.asset_id.id
        return res


class AccountInvoice(models.Model):
    _inherit = 'account.invoice'

    @api.multi
    def action_move_create(self):
        line_ids = []
        for invoice in self:
            for line in invoice.invoice_line:
                if line.asset_category_id and line.asset_category_id.asset_creation == 'auto':
                    line_ids.append(line.id)
        self.env['account.invoice.line'].browse(line_ids).create_assets()
        return super(AccountInvoice, self).action_move_create()

    @api.model
    def line_get_convert(self, invoice_line_info, partner_id, date):
        res = super(AccountInvoice, self).line_get_convert(invoice_line_info, partner_id, date)
        res['asset_id'] = invoice_line_info.get('asset_id', False)
        return res
