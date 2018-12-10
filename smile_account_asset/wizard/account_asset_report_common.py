# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.exceptions import ValidationError

from ..tools import get_period_stop_date, get_fiscalyear_start_date


class AccountAssetCommonReport(models.TransientModel):
    _name = 'account.asset.common.report'
    _description = 'Account Asset Common Report'

    date_from = fields.Date(
        'Start Date', required=True,
        default=lambda self: self._get_default_date_from())
    date_to = fields.Date(
        'End Date', required=True,
        default=lambda self: self._get_default_date_to())
    company_id = fields.Many2one(
        'res.company', 'Company', required=True,
        default=lambda self: self.env.user.company_id)
    category_ids = fields.Many2many(
        'account.asset.category', string='Categories')
    partner_ids = fields.Many2many(
        'res.partner', string='Suppliers', domain=[('supplier', '=', True)])
    account_ids = fields.Many2many('account.account', string='Accounts')
    is_posted = fields.Boolean('Is posted', default=True)

    @api.model
    def _get_default_date_from(self):
        """ Default start date is the first day of fiscalyear of end date
        """
        return get_fiscalyear_start_date(
            self._get_default_date_to(),
            self.env.user.company_id.fiscalyear_start_day)

    @api.model
    def _get_default_date_to(self):
        """ Default end date is the last day of previous period
        """
        company = self.env.user.company_id
        return get_period_stop_date(
            fields.Date.today(),
            company.fiscalyear_start_day,
            company.depreciation_period)

    @api.onchange('date_to', 'company_id')
    def _onchange_date_to(self):
        if self.date_to and self.company_id:
            self.date_from = get_fiscalyear_start_date(
                self.date_to, self.company_id.fiscalyear_start_day)

    @api.one
    @api.constrains('date_from', 'date_to')
    def _check_dates(self):
        if self.date_from and self.date_to and self.date_from > self.date_to:
            raise ValidationError(
                _("Start date can't be greater than stop date"))

    def _print_report(self, data):
        raise NotImplementedError()

    @api.multi
    def check_report(self):
        self.ensure_one()
        data = {}
        data['ids'] = self.env.context.get('active_ids', [])
        data['model'] = self.env.context.get('active_model', 'ir.ui.menu')
        data['form'] = self.read(load='_classic_write')[0]
        return self._print_report(data)
