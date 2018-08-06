# -*- coding: utf-8 -*-
# (C) 2013 Smile (<http://www.smile.fr>)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import models


class AccountTax(models.Model):
    _inherit = 'account.tax'

    def get_grouping_key(self, invoice_tax_val):
        res = super(AccountTax, self).get_grouping_key(invoice_tax_val)
        res += '-' + str(invoice_tax_val.get('deduction_rate', False))
        return res
