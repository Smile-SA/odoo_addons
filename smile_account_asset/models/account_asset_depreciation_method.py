# -*- coding: utf-8 -*-
# (C) 2019 Smile (<http://www.smile.fr>)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from dateutil.relativedelta import relativedelta

from odoo import api, fields, models, tools, _
from odoo.exceptions import UserError, ValidationError
from odoo.tools.safe_eval import safe_eval

from ..tools import get_fiscalyear_stop_date, get_period_stop_date, \
    DepreciationBoard


class AccountAssetDepreciationMethod(models.Model):
    _name = 'account.asset.depreciation.method'
    _description = 'Asset Depreciation Method'

    name = fields.Char(required=True, translate=True)
    code = fields.Char(required=True)
    depreciation_type = fields.Selection([
        ('accounting', 'Accounting'),
        ('fiscal', 'Fiscal'),
    ], 'Type', required=True)
    base_value = fields.Selection([
        ('purchase_value', 'Gross Value'),
        ('book_value', 'Book Value'),
    ], 'Base', required=True)
    use_salvage_value = fields.Boolean(
        'Take into account salvage value')
    depreciation_start_date = fields.Selection([
        ('in_service_date', 'In-service Date'),
        ('first_day_of_purchase_month',
         'First day of the month of purchase'),
    ], 'Start Date', required=True, default='in_service_date')
    depreciation_stop_date = fields.Selection([
        ('sale_date', 'Sale Date'),
        ('last_day_of_previous_sale_month',
         'Last day of the month prior to the sale'),
    ], 'End Date', required=True, default='sale_date')
    use_manual_rate = fields.Boolean(
        'Take into account depreciation rate indicated in asset')
    rate_formula = fields.Text(
        'Depreciation Rate', required=True,
        help="This expression is evaluated with length, annuity_number "
             "and rate (if depreciation rate indicated in asset) in localdict")
    prorata = fields.Boolean('Prorata Temporis', default=True)
    need_additional_annuity = fields.Boolean(
        'Need Additional Annuity',
        help="If depreciation start date is different "
             "from fiscalyear start date")

    _sql_constraints = [
        ('uniq_method', 'unique(code)', u'Method code must be unique!'),
    ]

    @api.one
    @api.constrains('rate_formula')
    def _check_depreciation_rate(self):
        localdict = {'length': 5, 'annuity_number': 1, 'pow': pow}
        if self.use_manual_rate:
            localdict['rate'] = 35.0
        try:
            safe_eval(self.rate_formula, localdict)
        except Exception:
            raise ValidationError(_('Bad depreciation rate formula'))

    @api.model
    def get_methods_selection(self, depreciation_type):
        methods = self.search([('depreciation_type', '=', depreciation_type)])
        return [('none', _('None'))] + \
            [(method['code'], method['name']) for method in methods] + \
            [('manual', _('Manual'))]

    @api.model
    def get_method_info(self, code):
        method_infos = self.get_method_infos()
        if code not in method_infos:
            raise UserError(_("The method code %s doesn't exist!") % code)
        return method_infos[code]

    @tools.ormcache()
    def get_method_infos(self):
        methods = {
            method['code']: method
            for method in self.search_read([], [])
        }
        special_methods = {
            'none': {
                'name': _('None'),
                'code': 'none',
                'base_value': 'book_value',
                'use_salvage_value': False,
                'depreciation_start_date': 'in_service_date',
                'depreciation_stop_date': 'sale_date',
                'use_manual_rate': False,
                'rate_formula': '0.0',
                'prorata': False,
                'need_additional_annuity': False,
            },
            'manual': {
                'name': _('Manual'),
                'code': 'manual',
                'base_value': 'book_value',
                'use_salvage_value': False,
                'depreciation_start_date': 'in_service_date',
                'depreciation_stop_date': 'sale_date',
                'use_manual_rate': False,
                'rate_formula': '0.0',
                'prorata': False,
                'need_additional_annuity': False
            },
        }
        methods.update(special_methods)
        return methods

    @api.model
    def create(self, vals):
        method = super(AccountAssetDepreciationMethod, self).create(vals)
        method.clear_caches()
        return method

    @api.multi
    def write(self, vals):
        res = super(AccountAssetDepreciationMethod, self).write(vals)
        self._update_assets(vals)
        self.clear_caches()
        return res

    @api.multi
    def _update_assets(self, vals):
        if 'use_manual_rate' in vals:
            for method in self:
                domain = [
                    ('%s_method' % method.depreciation_type, '=', method.code),
                ]
                vals = {
                    '%s_rate_visibility' % method.depreciation_type:
                    vals['use_manual_rate'],
                }
                for model in ['account.asset.category', 'account.asset.asset']:
                    self.env[model].search(domain).write(vals)

    @api.multi
    def unlink(self):
        self._can_unlink()
        res = super(AccountAssetDepreciationMethod, self).unlink()
        self.clear_caches()
        return res

    @api.one
    def _can_unlink(self):
        domain = [('%s_method' % self.depreciation_type, '=', self.code)]
        for model in ('account.asset.category', 'account.asset.asset'):
            if self.env[model].search(domain, limit=1):
                raise UserError(
                    _("You cannot unlink the method %s because it's used")
                    % self.name)

    @api.model
    def get_benefit_accelerated_depreciation(
            self, purchase_value, salvage_value, purchase_date,
            in_service_date,
            accounting_method, accounting_annuities, accounting_rate,
            fiscal_method, fiscal_annuities, fiscal_rate):
        first_accounting_annuity = self.compute_depreciation_board(
            accounting_method, purchase_value, salvage_value,
            accounting_annuities, accounting_rate, purchase_date,
            in_service_date)
        if not first_accounting_annuity:
            return False
        first_fiscal_annuity = self.compute_depreciation_board(
            fiscal_method, purchase_value, salvage_value,
            fiscal_annuities, fiscal_rate, purchase_date, in_service_date)
        if not first_fiscal_annuity:
            return False
        return first_fiscal_annuity[0]['depreciation_value'] > \
            first_accounting_annuity[0]['depreciation_value']

    @api.model
    def get_depreciation_start_date(
            self, code, purchase_date, in_service_date):
        method_info = self.get_method_info(code)
        if method_info['depreciation_start_date'] == \
                'first_day_of_purchase_month':
            date = purchase_date or fields.Date.today()
            return date.strftime('%Y-%m-01')
        return in_service_date or fields.Date.today()

    @api.model
    def get_depreciation_stop_date(
            self, code, purchase_date, in_service_date, annuities,
            depreciation_period=12, fiscalyear_start_day='01-01',
            exceptional_values=None):
        if code == 'none':
            return None
        method_info = self.get_method_info(code)
        date = fields.Date.from_string(self.get_depreciation_start_date(
            code, purchase_date, in_service_date))
        if not exceptional_values and method_info['need_additional_annuity']:
            date += relativedelta(years=annuities, days=-1)
            return get_period_stop_date(
                date, fiscalyear_start_day, depreciation_period). \
                strftime('%Y-%m-%d')
        period_stop_date = get_fiscalyear_stop_date(date, fiscalyear_start_day)
        period_stop_date += relativedelta(years=annuities - 1)
        return period_stop_date.strftime('%Y-%m-%d')

    @api.model
    def compute_depreciation_board(
            self, code, purchase_value, salvage_value, annuities, rate,
            purchase_date, in_service_date, sale_date=None,
            depreciation_period=12, fiscalyear_start_day='01-01',
            board_stop_date=None, rounding=2,
            readonly_values=None, exceptional_values=None):
        if not code or code == 'none':
            return []
        kwargs = locals().copy()
        kwargs['method_info'] = self.get_method_info(code)
        kwargs['depreciation_start_date'] = self.get_depreciation_start_date(
            code, purchase_date, in_service_date)
        for key in ('self', 'code', 'purchase_date', 'in_service_date'):
            del kwargs[key]
        company = self.env.user.company_id
        kwargs['prorata_temporis_exact'] = company.prorata_temporis == 'exact'
        kwargs['first_day_acquisition'] = company.first_day_acquisition
        board = DepreciationBoard(**kwargs)
        return [line.__dict__ for line in board.compute()]
