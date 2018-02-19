# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, models


class ResCompany(models.Model):
    _inherit = 'res.company'

    @api.model_cr
    def init(self):
        super(ResCompany, self).init()
        self._company_dependent_models.append('purchase.order')
