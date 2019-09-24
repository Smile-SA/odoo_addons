# -*- coding: utf-8 -*-
# (C) 2019 Smile (<http://www.smile.fr>)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import api, fields, models
from odoo.exceptions import UserError


class AccountAssetHistory(models.Model):
    _name = 'account.asset.history'
    _description = 'Asset history'
    _inherit = 'abstract.asset'
    _rec_name = 'asset_id'
    _order = 'date_to desc'

    date_to = fields.Datetime(
        'Until', readonly=True, default=fields.Datetime.now)
    user_id = fields.Many2one(
        'res.users', 'User', readonly=True, ondelete='restrict',
        default=lambda self: self._uid)
    asset_id = fields.Many2one(
        'account.asset.asset', 'Asset',
        required=True, ondelete='cascade', index=True, auto_join=True)
    category_id = fields.Many2one(
        'account.asset.category', 'Asset Category',
        required=True, ondelete='restrict')
    display_validation_warning = fields.Boolean(
        compute='_compute_display_validation_warning')
    company_id = fields.Many2one(
        related='asset_id.company_id', readonly=True)
    currency_id = fields.Many2one(
        related='asset_id.currency_id', readonly=True)
    purchase_value = fields.Monetary('Gross Value', required=True)
    salvage_value = fields.Monetary('Salvage Value')
    purchase_value_sign = fields.Monetary(
        'Gross Value', compute='_get_book_value', store=True)
    salvage_value_sign = fields.Monetary(
        'Salvage Value', compute='_get_book_value', store=True)
    purchase_tax_amount = fields.Monetary('Tax Amount', readonly=True)
    purchase_date = fields.Date(required=True, readonly=True)
    in_service_date = fields.Date('In-service Date')
    benefit_accelerated_depreciation = fields.Boolean(readonly=True)
    note = fields.Text('Reason')
    dummy = fields.Boolean(store=False)

    @api.one
    @api.depends('purchase_value', 'salvage_value', 'asset_id.asset_type')
    def _get_book_value(self):
        sign = self.asset_id.asset_type == 'purchase_refund' and -1 or 1
        self.purchase_value_sign = self.purchase_value * sign
        self.salvage_value_sign = self.salvage_value * sign

    @api.one
    @api.depends('category_id.asset_in_progress')
    def _compute_display_validation_warning(self):
        self.display_validation_warning = self._context.get(
            'asset_validation') and self.category_id.asset_in_progress

    @api.model
    def _get_fields_to_read(self):
        return list(set(self._fields.keys()) - set(models.MAGIC_COLUMNS)
                    & set(self.env['account.asset.asset']._fields.keys())
                    - {'old_id', '__last_update'})

    @api.onchange('asset_id')
    def _onchange_asset(self):
        for field in self._get_fields_to_read():
            self[field] = self.asset_id[field]

    @api.onchange('category_id')
    def _onchange_category(self):
        if self.dummy:
            for field in self.asset_id._category_fields:
                self[field] = self.category_id[field]
        else:
            self.dummy = True

    @api.model
    def create(self, vals):
        if self._context.get('data_integration'):
            return super(AccountAssetHistory, self).create(vals)
        # Update asset with vals and save old vals by creating a history record
        asset = self.env['account.asset.asset'].browse(vals['asset_id'])
        fields_to_read = self._get_fields_to_read()
        old_vals = asset.read(fields_to_read, load='_classic_write')[0]
        del old_vals['id']
        for field in dict(vals):
            if field not in fields_to_read:
                old_vals[field] = vals[field]
                del vals[field]
        asset.with_context(from_history=True).write(vals)
        asset.compute_depreciation_board()
        return super(AccountAssetHistory, self).create(old_vals)

    @api.multi
    def button_validate(self):
        if self._context.get('asset_validation'):
            asset = self.mapped('asset_id')
            try:
                asset.validate()
            except UserError:
                self.unlink()
                return asset.button_put_into_service()
        return {'type': 'ir.actions.act_window_close'}
