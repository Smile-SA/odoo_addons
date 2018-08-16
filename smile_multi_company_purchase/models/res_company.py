# -*- coding: utf-8 -*-
# (C) 2017 Smile (<http://www.smile.fr>)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import api, models


class ResCompany(models.Model):
    _inherit = 'res.company'

    @api.model_cr
    def init(self):
        super(ResCompany, self).init()
        self._invoicing_company_dependent_models.append('purchase.order')
