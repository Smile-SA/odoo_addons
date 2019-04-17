# -*- coding: utf-8 -*-
# (C) 2019 Smile (<http://www.smile.fr>)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields, models


class AccountMove(models.Model):
    _inherit = 'account.move'

    asset_depreciation_line_ids = fields.One2many(
        'account.asset.depreciation.line', 'move_id',
        'Asset Depreciation Lines', readonly=True)
