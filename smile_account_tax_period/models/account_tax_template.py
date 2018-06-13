# -*- coding: utf-8 -*-

from odoo import api, fields, models


class AccountTaxTemplate(models.Model):
    _inherit = 'account.tax.template'

    date_start = fields.Date('Start Date')
    date_stop = fields.Date('End Date')

    @api.multi
    def _get_tax_vals(self, company, tax_template_to_tax):
        self.ensure_one()
        vals = super(AccountTaxTemplate, self)._get_tax_vals(
            company, tax_template_to_tax)
        vals.update({
            'date_start': self.date_start,
            'date_stop': self.date_stop,
        })
        return vals
