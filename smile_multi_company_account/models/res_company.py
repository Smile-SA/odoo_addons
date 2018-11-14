# -*- coding: utf-8 -*-
# (C) 2018 Smile (<http://www.smile.eu>)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import api, fields, models


class ResCompany(models.Model):
    _inherit = 'res.company'
    _invoicing_company_dependent_models = ['account.invoice']

    is_invoicing_company = fields.Boolean(
        compute='_is_invoicing_company', store=True)

    @api.one
    @api.depends('chart_template_id')
    def _is_invoicing_company(self):
        self.is_invoicing_company = bool(self.chart_template_id)

    @api.multi
    def _get_invoicing_company(self):
        """
            If a company is not an invoicing company,
            this method returns the first invoicing company child
        """
        self.ensure_one()
        for child in self._get_all_children():
            if child.is_invoicing_company:
                return child
        return False

    @api.model
    def _company_default_get(self, object=False, field=False):
        company = super(ResCompany, self)._company_default_get(object, field)
        if object in self._invoicing_company_dependent_models:
            company = company._get_invoicing_company()
        return company or self.env.user.company_id
