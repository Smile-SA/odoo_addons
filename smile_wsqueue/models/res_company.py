# -*- coding: utf-8 -*-
# (C) 2021 Smile (<http://www.smile.fr>)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo import models, fields


class ResCompany(models.Model):
    _inherit = "res.company"

    email_wsqueue = fields.Char(string="Webservice error recipient")
