# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, models


class ResCompany(models.Model):
    _inherit = 'res.company'
    _company_dependent_models = ['account.invoice']

    @api.multi
    def _get_invoicing_company(self):
        """
            If a company has no chart of accounts,
            this method returns the first child having a chart of accounts
        """
        self.ensure_one()
        for child in self._get_all_children():
            if child.chart_template_id:
                return child
        return False

    @api.model
    def _company_default_get(self, object=False, field=False):
        company = super(ResCompany, self)._company_default_get(object, field)
        if object in self._company_dependent_models:
            company = company._get_invoicing_company()
        return company or self.env.user.company_id
