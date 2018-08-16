# -*- coding: utf-8 -*-
# (C) 2017 Smile (<http://www.smile.fr>)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields, models


class PurchaseOrder(models.Model):
    _inherit = 'purchase.order'

    company_id = fields.Many2one(domain=[('is_invoicing_company', '=', True)])
