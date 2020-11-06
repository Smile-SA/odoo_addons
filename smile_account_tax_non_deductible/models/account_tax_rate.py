# -*- coding: utf-8 -*-
# (C) 2013 Smile (<http://www.smile.fr>)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


class AccountTaxRate(models.Model):
    _name = 'account.tax.rate'
    _description = 'Account Tax Deduction Rate'
    _rec_name = 'rate_type'
    _order = 'start_date desc'

    rate_type = fields.Selection([
        ('admission', 'Admission'),
        ('subjugation', 'Subjugation'),
        ('taxation', 'Taxation'),
    ], required=True)
    start_date = fields.Date(
        default=fields.Date.context_today, required=True)
    value = fields.Float(digits=(5, 4))
    industry_id = fields.Many2one(
        'res.partner.industry', 'Industry')
    product_tmpl_id = fields.Many2one(
        'product.template', 'Product')

    @api.one
    @api.constrains('value')
    def _check_value(self):
        if self.value < 0 or self.value > 1:
            raise ValidationError(_('A rate may vary only between 0 and 1'))

    @api.one
    @api.constrains('rate_type', 'industry_id', 'product_tmpl_id')
    def _check_rate_type(self):
        if self.rate_type == 'taxation' and not self.industry_id:
            raise ValidationError(
                _('Taxation rate is specific to an industry'))
        if self.rate_type != 'taxation' and not self.product_tmpl_id:
            raise ValidationError(
                _('Admission and subjugation rates are specific to '
                  'a product'))

    @api.multi
    def _compute_rate(self, date=None):
        if not self:
            return None
        date = date or fields.Date.today()
        domain = [
            ('id', 'in', self.ids),
            ('rate_type', 'in', self.mapped('rate_type')),
            ('start_date', '<=', date),
        ]
        rate = self.search(domain, limit=1, order='start_date desc')
        return rate.value

    @api.model
    def _compute_deduction_rate(self, industry, product, date=None):
        """Compute 3 kinds of rates at the given date
        - If none of the rates exist: return 0.0
        - If one of the rates is equal to 0.0: return 0.0
        - Otherwise, return the multiplication of the defined rates
        """
        taxation_rate = industry.taxation_rate_ids._compute_rate(date) \
            if industry else 0.0
        admission_rate = product.admission_rate_ids._compute_rate(date)
        subjugation_rate = product.subjugation_rate_ids._compute_rate(date)
        if all(rate is None for rate in (
                taxation_rate, admission_rate, subjugation_rate)) or \
            any(rate == 0.0 for rate in (
                taxation_rate, admission_rate, subjugation_rate)):
            return 0
        taxation_rate = taxation_rate or 1.0
        admission_rate = admission_rate or 1.0
        subjugation_rate = subjugation_rate or 1.0
        return taxation_rate * admission_rate * subjugation_rate
