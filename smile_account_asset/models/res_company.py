# -*- coding: utf-8 -*-
# (C) 2019 Smile (<http://www.smile.fr>)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import api, fields, models

from ..tools import get_fiscalyear_start_date, get_fiscalyear_stop_date


class ResCompany(models.Model):
    _inherit = 'res.company'

    depreciation_period = fields.Selection([
        (1, 'Monthly'),
        (2, 'Bimonthly'),
        (3, '3-Monthly'),
        (4, '4-Monthly'),
        (6, 'Halfyearly'),
        (12, 'Yearly'),
    ], 'Depreciation Frequency', required=True, default=12)
    fiscal_depreciation_account_id = fields.Many2one(
        'account.account', 'Fiscal Depreciation Account',
        ondelete='restrict')
    fiscal_depreciation_expense_account_id = fields.Many2one(
        'account.account', 'Fiscal Depreciation Expense Account',
        ondelete='restrict')
    fiscal_depreciation_income_account_id = fields.Many2one(
        'account.account', 'Fiscal Depreciation Income Account',
        ondelete='restrict')
    exceptional_amortization_expense_account_id = fields.Many2one(
        'account.account', 'Exceptional Amortization Expense Account',
        ondelete='restrict',
        help="Use for transfer depreciations in amortizations")
    exceptional_amortization_income_account_id = fields.Many2one(
        'account.account', 'Exceptional Amortization Income Account',
        ondelete='restrict',
        help="Use for transfer depreciations in amortizations")
    prorata_temporis = fields.Selection([
        ('exact', '365'),
        ('approched', '360'),
    ], 'Prorata Temporis', required=True, default='approched')
    first_day_acquisition = fields.Boolean(
        'First day of acquisition', default=True)
    convert_book_value_if_scrapping = fields.Boolean(
        'Convert book value to exceptional depreciation if scrapping',
        default=True)
    fiscalyear_start_day = fields.Char(compute='_get_fiscalyear_start_day')

    @api.one
    def _get_fiscalyear_start_day(self):
        today = fields.Date.from_string(fields.Date.today())
        start_date = self.compute_fiscalyear_dates(today)['date_from']
        self.fiscalyear_start_day = fields.Date.to_string(start_date)[5:]

    @api.multi
    @api.returns('account.asset.depreciation.line',
                 lambda records: records.ids)
    def post_depreciation_lines(self, date=None):
        depreciation_lines = self._get_depreciation_lines_to_post(date)
        depreciation_lines.post_depreciation_line()
        return depreciation_lines

    @api.multi
    def _get_depreciation_lines_to_post(self, date):
        date = date or fields.Date.today()
        return self.env['account.asset.depreciation.line']. \
            search([
                ('company_id', 'in', self.ids),
                ('depreciation_date', '<=', date),
                ('is_posted', '=', False),
            ])

    @api.multi
    def create_inventory_entries(self, date=None):
        date = date or fields.Date.today()
        assets = self.env['account.asset.asset']
        for company in self:
            fiscalyear_start_date = fields.Date.to_string(
                get_fiscalyear_start_date(
                    date, company.fiscalyear_start_day))
            fiscalyear_stop_date = fields.Date.to_string(
                get_fiscalyear_stop_date(
                    date, company.fiscalyear_start_day))
            assets |= assets.search([
                ('sale_date', '>=', fiscalyear_start_date),
                ('sale_date', '<=', fiscalyear_stop_date),
                ('state', '=', 'close'),
                ('is_out', '=', False),
            ])
        return assets.output()

    @api.multi
    def write(self, vals):
        fnames = list(vals.keys())
        for company in self:
            old_vals = company.read(fnames, load='_classic_write')[0]
            if 'id' not in vals:
                del old_vals['id']
            self.env['account.asset.asset'].change_accounts(
                '%s,%s' % (self._name, company.id), old_vals, vals)
        return super(ResCompany, self).write(vals)
