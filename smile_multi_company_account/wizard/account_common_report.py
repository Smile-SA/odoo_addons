# -*- coding: utf-8 -*-
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import fields, models


class AccountCommonReport(models.TransientModel):
    _inherit = "account.common.report"

    company_id = fields.Many2one(domain=[('is_invoicing_company', '=', True)])
