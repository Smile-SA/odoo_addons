# -*- coding: utf-8 -*-
# (C) 2018 Smile (<http://www.smile.eu>)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields, models


class AccountCommonReport(models.TransientModel):
    _inherit = "account.common.report"

    company_id = fields.Many2one(domain=[('is_invoicing_company', '=', True)])
