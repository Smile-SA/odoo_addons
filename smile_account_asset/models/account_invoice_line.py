# -*- coding: utf-8 -*-
# (C) 2019 Smile (<http://www.smile.fr>)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from functools import partial

from odoo import api, fields, models, _
from odoo.exceptions import UserError


class AccountInvoiceLine(models.Model):
    _inherit = 'account.invoice.line'
    _asset_key_fields = ['asset_category_id', 'company_id',
                         'currency_id', 'partner_id', 'account_id',
                         'invoice_line_tax_ids']

    asset_category_id = fields.Many2one(
        'account.asset.category', 'Asset Category',
        ondelete='restrict', index=True, auto_join=True)
    asset_id = fields.Many2one(
        'account.asset.asset', 'Asset',
        readonly=True, ondelete='restrict',
        copy=False, index=True, auto_join=True)
    parent_id = fields.Many2one(
        'account.asset.asset', 'Parent Asset', ondelete='restrict')
    date_invoice = fields.Date(
        related='invoice_id.date_invoice', readonly=True, store=True)

    @api.onchange('asset_category_id')
    def _onchange_asset_category(self):
        self.account_id = self.asset_category_id.asset_account_id
        self.account_analytic_id = \
            self.asset_category_id.asset_analytic_account_id

    _auto_onchanges = {
        '_onchange_asset_category': ['account_id', 'account_analytic_id'],
    }

    @api.model
    def _update_vals(self, vals):
        for onchange_method, changed_fields in self._auto_onchanges.items():
            if any(field not in vals for field in changed_fields):
                new_record = self.new(vals)
                getattr(new_record, onchange_method)()
                for field in changed_fields:
                    if field not in vals and field in self._fields and \
                            new_record[field]:
                        vals[field] = new_record._fields[field]. \
                            convert_to_write(new_record[field], new_record)

    @api.model
    def create(self, vals):
        self._update_vals(vals)
        return super(AccountInvoiceLine, self).create(vals)

    @api.multi
    def write(self, vals):
        if self:
            self._update_vals(vals)
        return super(AccountInvoiceLine, self).write(vals)

    @api.multi
    def create_assets(self):
        for lines in self._group_by_asset():
            lines.with_context(do_not_check_invoice_lines=True).create_asset()
        return True

    @api.multi
    def _group_by_asset(self):
        res = {}
        for line in self:
            if line.asset_category_id and \
                    line.invoice_id.journal_id.type == 'purchase':
                asset_key = tuple([line[field]
                                   for field in self._asset_key_fields])
                res.setdefault(asset_key, self.browse())
                res[asset_key] |= line
        return res.values()

    @api.multi
    @api.returns('account.asset.asset', lambda record: record.id)
    def create_asset(self):
        lines = self.filtered(
            lambda line: not line.asset_id or line.asset_id.state == 'cancel')
        if not self._context.get('do_not_check_invoice_lines'):
            lines._check_before_creating_asset()
        if not lines:
            raise UserError(
                _('No asset to create from these invoice lines!'))
        asset = self.env['account.asset.asset'].create(lines._get_asset_vals())
        lines.write({'asset_id': asset.id})
        if lines.mapped('asset_category_id').confirm_asset:
            asset.confirm_asset_purchase()
        return asset

    @api.multi
    def _check_before_creating_asset(self):
        for field in self._asset_key_fields:
            if len(self.mapped(field)) > 1:
                label = self.env['ir.model.fields'].search([
                    ('name', '=', field),
                    ('model', '=', self._name),
                ], limit=1).field_description
                lang = self._context.get('lang') or self.env.user.lang
                translate = partial(
                    self.env['ir.translation']._get_source,
                    None, 'model', lang)
                label = '{}'.format(translate(label) or label)
                raise UserError(
                    _('You cannot not create an asset from invoice lines '
                      'with different %s') % label)
        for line in self:
            if line.invoice_id.type == 'in_refund' and not line.parent_id:
                raise UserError(
                    _('Please indicate a parent asset in line %s')
                    % line.name)

    @api.multi
    def _get_asset_vals(self):
        asset_type = 'purchase'
        amount = quantity = 0.0
        for line in self:
            sign = line.invoice_id.journal_id.type == 'purchase_refund' and \
                -1.0 or 1.0
            amount += line.price_subtotal * sign
            quantity += line.quantity * sign
        if amount < 0.0:
            amount = abs(amount)
            quantity = abs(quantity)
            asset_type = 'purchase_refund'
        line = self[0]
        vals = {
            'name': line.name,
            'parent_id': line.parent_id.id,
            'category_id': line.asset_category_id.id,
            'purchase_date': line.invoice_id.date_invoice or
            fields.Date.today(),
            'purchase_account_date': line.invoice_id.date_invoice,
            'purchase_value': amount,
            'quantity': quantity,
            'asset_type': asset_type,
            'supplier_id': line.partner_id.id,
            'company_id': line.company_id.id,
            'currency_id': line.currency_id.id,
            'purchase_tax_ids': [(6, 0, line.invoice_line_tax_ids.ids)],
        }
        for field in self.env['account.asset.asset']._category_fields:
            if isinstance(line.asset_category_id[field], models.BaseModel):
                vals[field] = line.asset_category_id[field].id
            else:
                vals[field] = line.asset_category_id[field]
        return vals
