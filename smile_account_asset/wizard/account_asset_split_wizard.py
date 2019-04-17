# -*- coding: utf-8 -*-
# (C) 2019 Smile (<http://www.smile.fr>)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import api, fields, models, _
from odoo.exceptions import ValidationError
from odoo.tools import float_round
from odoo.tools.safe_eval import safe_eval


class AccountAssetSplitWizard(models.TransientModel):
    _name = 'account.asset.split_wizard'
    _description = 'Asset Split Wizard'
    _rec_name = 'asset_id'

    asset_id = fields.Many2one(
        'account.asset.asset', 'Asset', required=True, ondelete='cascade')
    currency_id = fields.Many2one(
        related='asset_id.currency_id', readonly=True)
    new_asset_id = fields.Many2one(
        'account.asset.asset', 'New Asset', readonly=True, ondelete='cascade')
    initial_purchase_value = fields.Monetary(
        related='asset_id.purchase_value', readonly=True)
    initial_salvage_value = fields.Monetary(
        related='asset_id.salvage_value', readonly=True)
    initial_quantity = fields.Float(
        related='asset_id.quantity', readonly=True)
    purchase_value = fields.Monetary('Gross Value', required=True)
    salvage_value = fields.Monetary('Salvage Value', required=True)
    quantity = fields.Float('Quantity', required=True)

    @api.one
    @api.constrains('quantity')
    def _check_quantity(self):
        if not self._check_split('quantity'):
            raise ValidationError(
                _('You must specify a positive quantity lower than '
                  'the initial one!'))

    @api.one
    @api.constrains('purchase_value', 'salvage_value')
    def _check_purchase_value(self):
        if not self._check_split('purchase_value', '>='):
            raise ValidationError(
                _('You must specify a positive gross value lower than '
                  'the initial one!'))
        if not self._check_split('salvage_value'):
            raise ValidationError(
                _('You must specify a positive salvage value lower than '
                  'the initial one!'))
        if self.salvage_value > self.purchase_value:
            raise ValidationError(
                _('You must specify a salvage value lower than gross value!'))

    @api.multi
    def _check_split(self, field, operator='>'):
        self.ensure_one()
        if self[field] < 0.0:
            return False
        expr = '%(new_value)s %(operator)s %(old_value)s'
        context = {
            'old_value': self.asset_id[field],
            'new_value': self[field],
            'operator': operator,
        }
        if safe_eval(expr % context):
            return False
        return True

    @api.onchange('asset_id')
    def onchange_asset_id(self):
        self.purchase_value = self.asset_id.purchase_value
        self.quantity = self.asset_id.quantity

    @api.multi
    def button_validate(self):
        self.validate()
        return {'type': 'ir.actions.act_window_close'}

    @api.multi
    def validate(self):
        self._split_asset(*self._get_vals_and_default())
        return True

    @api.multi
    def _get_vals_and_default(self):
        self.ensure_one()
        default = {
            'parent_id': self.asset_id.id,
            'origin_id': self.asset_id.id,
            'purchase_value': self.purchase_value,
            'salvage_value': self.salvage_value,
        }
        vals = {
            'purchase_value':
            self.asset_id.purchase_value - self.purchase_value,
            'salvage_value': self.asset_id.salvage_value - self.salvage_value,
        }
        if self.quantity != self.asset_id.quantity:
            default['quantity'] = self.quantity
            vals['quantity'] = self.asset_id.quantity - self.quantity
        return vals, default

    @api.multi
    def _split_asset(self, vals, default):
        self.ensure_one()
        self = self.with_context(asset_split=True)
        self.new_asset_id = self.asset_id.copy(default)
        self.asset_id.write(vals)
        # Save journal entries before deleting depreciation lines
        moves_by_depreciation = {
            (line.depreciation_type, line.depreciation_date): line.move_id
            for line in self.asset_id.depreciation_line_ids
            if line.move_id and line.depreciation_type != 'exceptional'
        }
        (self.asset_id.accounting_depreciation_line_ids |
            self.asset_id.fiscal_depreciation_line_ids).unlink()
        self.asset_id.compute_depreciation_board()
        if self.asset_id.state == 'draft':
            self.new_asset_id.compute_depreciation_board()
        else:
            self.new_asset_id.confirm_asset_purchase()
            if self.asset_id.state == 'open':
                self.new_asset_id.validate()
            # Link journal entries to new depreciation lines
            rounding = self.asset_id.currency_id.decimal_places
            for asset in (self.asset_id, self.new_asset_id):
                for line in asset.depreciation_line_ids:
                    key = (line.depreciation_type, line.depreciation_date)
                    if key in moves_by_depreciation:
                        line.move_id = moves_by_depreciation[key]
                        # Regularize the depreciation lines of new assets
                        if asset == self.new_asset_id:
                            value_field = 'depreciation_value'
                            if line.depreciation_type == 'fiscal':
                                value_field = 'accelerated_value'
                            gap = float_round(line.move_id.amount - sum(
                                line.move_id.asset_depreciation_line_ids.
                                mapped(value_field)),
                                precision_digits=rounding)
                            if gap:
                                line.depreciation_value += gap
