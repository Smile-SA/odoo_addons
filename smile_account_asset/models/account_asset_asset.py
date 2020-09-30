# -*- coding: utf-8 -*-
# (C) 2019 Smile (<http://www.smile.fr>)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from dateutil.relativedelta import relativedelta
import time

from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError
from odoo.osv import expression

from odoo.tools.safe_eval import safe_eval

from ..tools import get_period_stop_date

ACCOUNT_GROUPS = {
    'asset_account_id': 'purchase',
    'asset_analytic_account_id': 'purchase',

    'accounting_depreciation_account_id': 'accounting_depreciation',
    'accounting_depreciation_expense_account_id': 'accounting_depreciation',
    'accounting_depreciation_income_account_id': 'accounting_depreciation',

    'fiscal_depreciation_account_id': 'fiscal_depreciation',
    'fiscal_depreciation_expense_account_id': 'fiscal_depreciation',
    'fiscal_depreciation_income_account_id': 'fiscal_depreciation',

    'exceptional_depreciation_account_id': 'exceptional_depreciation',
    'exceptional_depreciation_expense_account_id': 'exceptional_depreciation',
    'exceptional_depreciation_income_account_id': 'exceptional_depreciation',

    'exceptional_amortization_expense_account_id': 'exceptional_amortization',
    'exceptional_amortization_income_account_id': 'exceptional_amortization',
}
ASSET_STATES = [
    ('draft', 'Draft'),
    ('confirm', 'Acquised Or In progress'),
    ('open', 'Into service'),
    ('close', 'Sold Or Scrapped'),
    ('cancel', 'Cancelled'),
]
ASSET_TYPES = [
    ('purchase', 'Purchase'),
    ('purchase_refund', 'Purchase Refund'),
]


class AccountAssetAsset(models.Model):
    _name = 'account.asset.asset'
    _description = 'Asset'
    _inherit = ['abstract.asset', 'mail.thread', 'mail.activity.mixin']
    _parent_store = True
    _category_fields = [
        'accounting_method', 'accounting_annuities', 'accounting_rate',
        'fiscal_method', 'fiscal_annuities', 'fiscal_rate', 'company_id']
    _sale_fields = [
        'customer_id', 'sale_date', 'sale_account_date', 'sale_value',
        'sale_type', 'sale_result', 'sale_result_short_term',
        'sale_result_long_term',
        'tax_regularization', 'regularization_tax_amount', 'is_out']

    @api.model
    def _get_default_currency(self):
        return self.env.user.company_id.currency_id.id

    @api.model
    def _get_default_uom(self):
        return self.env.ref(
            'uom.product_uom_unit', raise_if_not_found=False).id

    name = fields.Char(
        readonly=True, states={'draft': [('readonly', False)]})
    code = fields.Char('Reference', readonly=True, copy=False)
    state = fields.Selection(
        ASSET_STATES, 'Status', readonly=True, default='draft')
    parent_id = fields.Many2one(
        'account.asset.asset', 'Parent Asset',
        readonly=True, states={'draft': [('readonly', False)]},
        ondelete='restrict', index=True)
    parent_path = fields.Char(index=True)
    child_ids = fields.One2many(
        'account.asset.asset', 'parent_id', 'Child Assets', copy=False)
    origin_id = fields.Many2one(
        'account.asset.asset', 'Origin Asset', copy=False,
        readonly=True, ondelete='restrict')
    category_id = fields.Many2one(
        'account.asset.category', 'Asset Category', required=True,
        readonly=True, states={'draft': [('readonly', False)]},
        ondelete='restrict')
    asset_in_progress = fields.Boolean(
        related='category_id.asset_in_progress', readonly=True)
    company_id = fields.Many2one(
        related='category_id.company_id', store=True, readonly=True)
    # CHANGE: allow to update anytime currency and offer a button
    # to update asset after currency change, like in invoice form
    currency_id = fields.Many2one(
        'res.currency', 'Currency', required=True, ondelete='restrict',
        readonly=True, states={'draft': [('readonly', False)]},
        default=_get_default_currency)
    asset_type = fields.Selection(
        ASSET_TYPES, "Type", required=True, default='purchase',
        readonly=True, states={'draft': [('readonly', False)]})
    supplier_id = fields.Many2one(
        'res.partner', 'Vendor', required=True, ondelete='restrict',
        readonly=True, states={
            'draft': [('readonly', False)],
            'confirm': [('readonly', False)],
        },
        domain=[('supplier', '=', True)])
    purchase_date = fields.Date(
        'Purchase Date', required=True,
        readonly=True, states={
            'draft': [('readonly', False)],
            'confirm': [('readonly', False)],
        })
    purchase_value = fields.Monetary(
        'Gross Value', required=True,
        readonly=True, states={'draft': [('readonly', False)]})
    salvage_value = fields.Monetary(
        'Salvage Value',
        readonly=True, states={'draft': [('readonly', False)]})
    book_value = fields.Monetary(
        'Book Value', compute='_get_book_value', store=True)
    book_value_sign = fields.Monetary(
        'Book Value', compute='_get_book_value', store=True)
    purchase_value_sign = fields.Monetary(
        'Gross Value', compute='_get_book_value', store=True)
    salvage_value_sign = fields.Monetary(
        'Salvage Value', compute='_get_book_value', store=True)
    accounting_method = fields.Selection(
        readonly=True, states={
            'draft': [('readonly', False)],
            'confirm': [('readonly', False)],
        })
    accounting_annuities = fields.Integer(
        required=False, readonly=True, states={
            'draft': [('readonly', False)],
            'confirm': [('readonly', False)],
        })
    accounting_rate = fields.Float(
        readonly=True, states={
            'draft': [('readonly', False)],
            'confirm': [('readonly', False)],
        })
    fiscal_method = fields.Selection(
        readonly=True, states={
            'draft': [('readonly', False)],
            'confirm': [('readonly', False)],
        })
    fiscal_annuities = fields.Integer(
        required=False, readonly=True, states={
            'draft': [('readonly', False)],
            'confirm': [('readonly', False)],
        })
    fiscal_rate = fields.Float(
        readonly=True, states={
            'draft': [('readonly', False)],
            'confirm': [('readonly', False)],
        })
    benefit_accelerated_depreciation = fields.Boolean(
        compute='_get_benefit_accelerated_depreciation',
        inverse='_set_benefit_accelerated_depreciation',
        readonly=True, states={
            'draft': [('readonly', False)],
            'confirm': [('readonly', False)],
        }, store=True)
    force_benefit_accelerated_depreciation = fields.Boolean(readonly=True)
    in_service_date = fields.Date(
        'In-service Date', readonly=True, states={
            'draft': [('readonly', False)],
            'confirm': [('readonly', False)],
        })
    depreciation_line_ids = fields.One2many(
        'account.asset.depreciation.line', 'asset_id',
        'Depreciation Lines', readonly=True, copy=False)
    accounting_depreciation_line_ids = fields.One2many(
        'account.asset.depreciation.line', 'asset_id',
        'Accounting Depreciations',
        domain=[('depreciation_type', '=', 'accounting')], copy=False)
    fiscal_depreciation_line_ids = fields.One2many(
        'account.asset.depreciation.line', 'asset_id',
        'Fiscal Depreciations',
        domain=[('depreciation_type', '=', 'fiscal')], copy=False)
    exceptional_depreciation_line_ids = fields.One2many(
        'account.asset.depreciation.line', 'asset_id',
        'Exceptional Depreciations', readonly=True,
        domain=[('depreciation_type', '=', 'exceptional')], copy=False)
    quantity = fields.Float(
        'Quantity', required=True, default=1.0,
        readonly=True, states={'draft': [('readonly', False)]})
    uom_id = fields.Many2one(
        'product.uom', 'Unit of Measure', required=True, ondelete='restrict',
        default=_get_default_uom,
        readonly=True, states={'draft': [('readonly', False)]})
    purchase_tax_ids = fields.Many2many(
        'account.tax', 'account_asset_asset_account_tax_purchase_rel',
        'asset_id', 'tax_id', 'Purchase Taxes',
        domain=[('type_tax_use', '!=', 'sale')],
        readonly=True, states={'draft': [('readonly', False)]})
    purchase_tax_amount = fields.Monetary(
        'Tax amount', compute='_get_purchase_tax_amount')
    asset_history_ids = fields.One2many(
        'account.asset.history', 'asset_id', 'History',
        readonly=True, copy=False)
    account_move_line_ids = fields.One2many(
        'account.move.line', 'asset_id', 'Journal Items',
        readonly=True, copy=False)
    invoice_line_ids = fields.One2many(
        'account.invoice.line', 'asset_id', 'Invoice Lines',
        readonly=True, copy=False)
    customer_id = fields.Many2one(
        'res.partner', 'Customer', ondelete='restrict',
        domain=[('customer', '=', True)], copy=False,
        readonly=True, states={'open': [('readonly', False)]})
    sale_date = fields.Date(
        'Sale Date', copy=False,
        readonly=True, states={'open': [('readonly', False)]})
    sale_value = fields.Monetary(
        'Sale Value', copy=False,
        readonly=True, states={'open': [('readonly', False)]})
    fiscal_book_value = fields.Monetary(
        'Fiscal Book Value', copy=False, readonly=True)
    accumulated_amortization_value = fields.Monetary(
        'Accumulated Amortization Value', copy=False, readonly=True)
    sale_type = fields.Selection(
        [('sale', 'Sale'), ('scrapping', 'Scrapping')], 'Disposal Type',
        readonly=True, states={'open': [('readonly', False)]}, copy=False)
    sale_result = fields.Monetary('Sale Result', readonly=True, copy=False)
    sale_result_short_term = fields.Monetary(
        'Sale Result - Short Term', readonly=True, copy=False)
    sale_result_long_term = fields.Monetary(
        'Sale Result - Long Term', readonly=True, copy=False)
    sale_tax_ids = fields.Many2many(
        'account.tax', 'account_asset_asset_account_tax_sale_rel',
        'asset_id', 'tax_id', 'Sale Taxes', copy=False,
        domain=[('type_tax_use', '!=', 'purchase')],
        readonly=True, states={'open': [('readonly', False)]})
    sale_tax_amount = fields.Monetary(
        'Tax Amount', compute='_get_sale_tax_amount')
    sale_invoice_number = fields.Char('Invoice Number', copy=False)
    tax_regularization = fields.Boolean(
        'Tax regularization', readonly=True, copy=False)
    regularization_tax_amount = fields.Monetary(
        'Tax amount to regularize', readonly=True, copy=False)
    is_out = fields.Boolean('Is Out Of Heritage', copy=False)
    number = fields.Char(
        related='invoice_line_ids.invoice_id.number', readonly=True)

    asset_account_id = fields.Many2one(
        'account.account', 'Asset Account',
        compute='_get_asset_account', store=True)
    sale_receivable_account_id = fields.Many2one(
        'account.account', 'Disposal Receivable Account',
        compute='_get_sale_receivable_account', store=True)
    purchase_account_date = fields.Date(
        'Accounting date for purchase', copy=False,
        readonly=True, states={'draft': [('readonly', False)]},
        help="Keep empty to use the current date")
    sale_account_date = fields.Date(
        'Accounting date for sale', copy=False,
        readonly=True, states={'open': [('readonly', False)]},
        help="Keep empty to use the current date")
    purchase_move_id = fields.Many2one(
        'account.move', 'Purchase Journal Entry', readonly=True, copy=False)
    sale_move_id = fields.Many2one(
        'account.move', 'Sale Journal Entry', readonly=True, copy=False)
    purchase_cancel_move_id = fields.Many2one(
        'account.move', 'Purchase Cancellation Journal Entry',
        readonly=True, copy=False)
    sale_cancel_move_id = fields.Many2one(
        'account.move', 'Sale Cancellation Journal Entry',
        readonly=True, copy=False)
    in_service_account_date = fields.Date(
        'Entry into service date', copy=False,
        readonly=True, states={'draft': [('readonly', False)],
                               'confirm': [('readonly', False)]})

    @api.one
    @api.depends('purchase_value', 'salvage_value',
                 'depreciation_line_ids.is_posted_forced',
                 'depreciation_line_ids.move_id')
    def _get_book_value(self):
        # Book Value =
        # + Gross Value
        # - Sum of accounting depreciations
        # - Sum of exceptional depreciations
        book_value = self.purchase_value
        for line in self.depreciation_line_ids:
            if line.depreciation_type != 'fiscal' and \
                    (line.is_posted or line.move_id):
                book_value -= line.depreciation_value
        sign = self.asset_type == 'purchase_refund' and -1 or 1
        self.book_value = book_value
        self.book_value_sign = self.book_value * sign
        self.purchase_value_sign = self.purchase_value * sign
        self.salvage_value_sign = self.salvage_value * sign

    @api.one
    @api.depends('purchase_value', 'purchase_tax_ids')
    def _get_purchase_tax_amount(self):
        res = self.purchase_tax_ids.compute_all(self.purchase_value)
        self.purchase_tax_amount = res['total_included'] - \
            res['total_excluded']

    @api.one
    @api.depends('sale_value', 'sale_tax_ids')
    def _get_sale_tax_amount(self):
        res = self.sale_tax_ids.compute_all(self.sale_value)
        self.sale_tax_amount = res['total_included'] - res['total_excluded']

    @api.one
    @api.depends('category_id.asset_account_id')
    def _get_asset_account(self):
        if self.state not in ['draft', 'confirm'] and \
                not self._context.get('from_history'):
            # Keep current value
            account_id = self.browse(self.id).read(
                ['asset_account_id'])[0]['asset_account_id'][0]
            self.asset_account_id = account_id
        else:
            self.asset_account_id = self.category_id.asset_account_id

    @api.one
    @api.depends(('category_id', [('state', 'not in', ('close', 'cancel'))]))
    def _get_sale_receivable_account(self):
        self.sale_receivable_account_id = \
            self.category_id.sale_receivable_account_id

    @api.one
    @api.depends('purchase_value', 'salvage_value',
                 'purchase_date', 'in_service_date', 'accounting_method',
                 'accounting_annuities', 'accounting_rate',
                 'fiscal_method', 'fiscal_annuities', 'fiscal_rate')
    def _get_benefit_accelerated_depreciation(self):
        self.benefit_accelerated_depreciation = \
            self.force_benefit_accelerated_depreciation or \
            self.env['account.asset.depreciation.method']. \
            get_benefit_accelerated_depreciation(
                self.purchase_value, self.salvage_value, self.purchase_date,
                self.in_service_date, self.accounting_method,
                self.accounting_annuities, self.accounting_rate,
                self.fiscal_method, self.fiscal_annuities, self.fiscal_rate)

    @api.one
    def _set_benefit_accelerated_depreciation(self):
        self.force_benefit_accelerated_depreciation = \
            self.benefit_accelerated_depreciation

    @api.one
    @api.constrains('parent_id')
    def _check_hierarchy(self):
        if not self._check_recursion():
            raise ValidationError(_('You cannot create recursive assets!'))

    @api.one
    @api.constrains('accounting_rate', 'fiscal_rate')
    def _check_rates(self):
        for field in ('accounting_rate', 'fiscal_rate'):
            rate = self[field]
            if rate < 0 or rate > 100:
                raise ValidationError(
                    _('Amortization rates must be percentages!'))

    @api.one
    @api.constrains('asset_type', 'parent_id')
    def _check_asset_type(self):
        if self.asset_type == 'purchase_refund' and not self.parent_id:
            raise ValidationError(
                _('Purchase refund is possible only for secondary assets'))

    @api.one
    @api.constrains('quantity')
    def _check_quantity(self):
        if self.quantity < 0:
            raise ValidationError(_('Quantity cannot be negative!'))

    @api.one
    @api.constrains('purchase_value')
    def _check_purchase_value(self):
        if self.purchase_value < 0.0:
            raise ValidationError(
                _('Purchase value cannot be negative'))

    @api.one
    @api.constrains('salvage_value', 'purchase_value')
    def _check_salvage_value(self):
        if self.salvage_value < 0.0 or \
                self.salvage_value > self.purchase_value:
            raise ValidationError(
                _('Salvage value cannot be negative '
                  'nor bigger than gross value!'))

    @api.onchange('category_id')
    def _onchange_category(self):
        for field in self._category_fields:
            self[field] = self.category_id[field]

    @api.onchange('company_id')
    def _onchange_company(self):
        self.currency_id = self.company_id.currency_id

    @api.multi
    def write(self, vals):
        self._change_accounts_from_category(vals)
        return super(AccountAssetAsset, self).write(vals)

    @api.one
    def _change_accounts_from_category(self, vals):
        if vals.get('category_id') and self.state != 'draft':
            old_category = self.category_id
            new_category = old_category.browse(vals['category_id'])
            if new_category != old_category:
                self.change_accounts(
                    '%s,%s' % (self._name, self.id),
                    old_category.read(load='_classic_write')[0],
                    new_category.read(load='_classic_write')[0])

    @api.one
    def name_get(self):
        return self.id, '[%s] %s' % (self.code, self.name)

    @api.model
    def name_search(self, name, args=None, operator='ilike', limit=100):
        args = [
            ('name', operator, name),
            ('code', operator, name),
        ] + (args or [])
        if operator not in expression.NEGATIVE_TERM_OPERATORS:
            args = ['|'] + args
        return self.search(args, limit=limit).name_get()

    @api.multi
    def compute_depreciation_board(self):
        self._compute_depreciation_lines('accounting')
        self._compute_depreciation_lines('fiscal')
        return True

    @api.one
    def _compute_depreciation_lines(self, depreciation_type='accounting'):
        self = self.sudo()
        DepreciationLine = self.env['account.asset.depreciation.line']
        # Delete old lines
        DepreciationLine.search([
            ('asset_id', '=', self.id),
            ('depreciation_type', '=', depreciation_type),
            ('is_posted', '=', False),
            ('asset_id.%s_method' % depreciation_type, '!=', 'manual')
        ]).unlink()
        # Inactivate posted lines with a depreciation date > board end date
        kwargs = self._get_depreciation_arguments(depreciation_type)
        operator = '>'
        if self.depreciation_line_ids and \
                kwargs['board_stop_date'] < self.depreciation_line_ids[
                    -1].depreciation_date.isoformat():
            operator = '>='  # Because amount will change
        context = dict(self._context)
        max_date = kwargs['board_stop_date']
        if kwargs.get('sale_date'):
            context['force_account_move_date'] = self.sale_account_date or \
                fields.Date.today()
            max_date = kwargs['sale_date']
            if not kwargs['last_day_of_previous_sale_month']:
                operator = '>='
        del kwargs['last_day_of_previous_sale_month']
        DepreciationLine.search([
            ('asset_id', '=', self.id),
            ('depreciation_type', '=', depreciation_type),
            ('depreciation_date', operator, max_date),
            ('is_posted', '=', True),
        ]).with_context(**context).write({'active': False})
        for depreciation_date in list(kwargs['readonly_values'].keys()):
            expr = "'%s' %s '%s'" % (depreciation_date, operator, max_date)
            if safe_eval(expr):
                del kwargs['readonly_values'][depreciation_date]
        # Create new lines
        line_infos = self.env['account.asset.depreciation.method']. \
            compute_depreciation_board(**kwargs)
        return self._update_or_create_depreciation_lines(
            line_infos, depreciation_type)

    @api.multi
    def _get_depreciation_arguments(self, depreciation_type):
        self.ensure_one()
        method = self['%s_method' % depreciation_type]
        depreciation_period = self.company_id.depreciation_period
        fiscalyear_start_day = self.company_id.fiscalyear_start_day
        readonly_values = {}
        exceptional_values = {}
        for line in self.depreciation_line_ids:
            period_stop_month = get_period_stop_date(
                line.depreciation_date, fiscalyear_start_day,
                depreciation_period).strftime('%Y-%m')
            if line.depreciation_type == depreciation_type and \
                    (line.is_posted or method == 'manual'):
                readonly_values.setdefault(
                    period_stop_month,
                    {'depreciation_value': 0.0, 'base_value': 0.0})
                readonly_values[period_stop_month]['depreciation_value'] += \
                    line.depreciation_value
                readonly_values[period_stop_month]['base_value'] = \
                    line.base_value
            elif line.depreciation_type == 'exceptional':
                exceptional_values.setdefault(period_stop_month, 0.0)
                exceptional_values[period_stop_month] += \
                    line.depreciation_value
        Method = self.env['account.asset.depreciation.method']
        accounting_stop_date = Method.get_depreciation_stop_date(
            self.accounting_method, self.purchase_date,
            self.in_service_date, self.accounting_annuities,
            depreciation_period, fiscalyear_start_day, exceptional_values)
        fiscal_stop_date = Method.get_depreciation_stop_date(
            self.fiscal_method, self.purchase_date,
            self.in_service_date, self.fiscal_annuities,
            depreciation_period, fiscalyear_start_day, exceptional_values)
        if not fiscal_stop_date:
            board_stop_date = accounting_stop_date
        else:
            board_stop_date = max(accounting_stop_date, fiscal_stop_date)
        sale_date = self.sale_date
        last_day_of_previous_sale_month = False
        if sale_date:
            method_info = Method.get_method_info(self.accounting_method)
            if method_info['depreciation_stop_date'] == \
                    'last_day_of_previous_sale_month':
                last_day_of_previous_sale_month = True
                sale_date = fields.Date.to_string(
                    fields.Date.from_string(sale_date)
                    + relativedelta(day=1)
                    + relativedelta(days=-1))
        return {
            'code': method,
            'purchase_value': self.purchase_value,
            'salvage_value': self.salvage_value,
            'annuities': self['%s_annuities' % depreciation_type],
            'rate': self['%s_rate' % depreciation_type],
            'purchase_date': self.purchase_date,
            'in_service_date': self.in_service_date,
            'sale_date': sale_date,
            'last_day_of_previous_sale_month': last_day_of_previous_sale_month,
            'depreciation_period': depreciation_period,
            'fiscalyear_start_day': fiscalyear_start_day,
            'rounding': self.currency_id.decimal_places,
            'board_stop_date': board_stop_date,
            'readonly_values': readonly_values,
            'exceptional_values': exceptional_values,
        }

    @api.one
    def _update_or_create_depreciation_lines(
            self, line_infos, depreciation_type):
        is_manual = self['%s_method' % depreciation_type] == 'manual'
        lines_to_create = []
        for vals in line_infos:
            vals.update({
                'asset_id': self.id,
                'depreciation_type': depreciation_type,
                'depreciation_date':
                    vals['depreciation_date'].strftime('%Y-%m-%d'),
                'active': True,
            })
            readonly = vals['readonly']
            del vals['readonly']
            if readonly:
                if is_manual:
                    dlines = self[
                        '%s_depreciation_line_ids' % depreciation_type]
                    for dline in dlines:
                        if dline.depreciation_date == \
                                vals['depreciation_date']:
                            dline.write(vals)
                            break
                continue
            lines_to_create.append(vals)
        if lines_to_create:
            self.env['account.asset.depreciation.line'].bulk_create(
                lines_to_create)

    @api.multi
    def button_confirm_asset_purchase(self):
        return self.confirm_asset_purchase()

    @api.multi
    def confirm_asset_purchase(self):
        assets_with_purchase_account_date = self.filtered(
            lambda asset: asset.purchase_account_date)
        vals = {
            'state': 'confirm',
            'code': self.env['ir.sequence'].next_by_code(self._name),
        }
        assets_with_purchase_account_date.write(vals)
        assets_without_purchase_account_date = self - \
            assets_with_purchase_account_date
        vals['purchase_account_date'] = fields.Date.today()
        assets_without_purchase_account_date.write(vals)
        if not self._context.get('asset_split'):
            for asset in self:
                # Case of direct creation
                if not asset.invoice_line_ids and (
                        not asset.origin_id or
                        not asset.origin_id.invoice_line_ids):
                    asset.create_move('purchase')
        if self.mapped('child_ids'):
            self.mapped('child_ids').confirm_asset_purchase()
        return True

    @api.multi
    def create_move(self, move_type, reverse=False):
        if not self:
            return True
        assert move_type in ('purchase', 'sale'), \
            "move_type must be equal to 'purchase' or 'sale'"
        moves = self.env['account.move']
        for asset in self:
            vals = asset._get_move_vals(move_type, reverse)
            if vals['line_ids']:
                move = moves.create(vals)
                field = '%s%s_move_id' % (
                    move_type, reverse and '_cancel' or '')
                asset.write({field: move.id})
                moves |= move
        return moves.post() if moves else True

    @api.multi
    def _get_move_vals(self, move_type, reverse=False):
        self.ensure_one()
        journal = self.category_id.asset_journal_id
        if move_type == 'purchase':
            move_date = self.purchase_account_date
            partner_id = self.supplier_id.id
            msg = _('Asset Purchase: %s')
        if move_type == 'sale':
            move_date = self.sale_account_date
            partner_id = self.customer_id.id
            msg = _('Asset Sale: %s')
            if self.category_id.sale_journal_id:
                journal = self.category_id.sale_journal_id
        if self._context.get('force_account_move_date'):
            move_date = self._context['force_account_move_date']
        if not move_date or reverse:
            move_date = fields.Date.today()
        vals = {
            'name': journal.sequence_id.with_context(
                ir_sequence_date=move_date).next_by_id(),
            'narration': msg % self.name,
            'ref': self.code,
            'date': move_date,
            'journal_id': journal.id,
            'partner_id': partner_id,
            'company_id': self.company_id.id,
        }
        default = vals.copy()
        default['currency_id'] = self.currency_id.id
        kwargs = self._get_move_line_kwargs(move_type, reverse)
        line_vals = self._get_move_line_vals(default=default, **kwargs)
        vals['line_ids'] = [(0, 0, x) for x in line_vals]
        return vals

    @api.multi
    def _get_move_line_kwargs(self, move_type, reverse=False):
        self.ensure_one()
        sign = reverse and -1 or 1
        if move_type == 'purchase':
            return {
                'journal_type': self.asset_type,
                'amount_excl_tax': self.purchase_value * sign,
                'tax_amount': self.purchase_tax_amount * sign,
                'taxes': self.purchase_tax_ids,
                'accounts': {
                    'asset_account_id':
                    self.category_id.asset_account_id.id,
                    'partner_account_id':
                    self.supplier_id.property_account_payable_id.id,
                    'analytic_account_id':
                    self.category_id.asset_analytic_account_id.id,
                },
            }
        else:
            return {
                'journal_type':
                self.asset_type == 'purchase' and 'sale' or 'sale_refund',
                'amount_excl_tax': self.sale_value * sign,
                'tax_amount': self.sale_tax_amount * sign,
                'taxes': self.sale_tax_ids,
                'accounts': {
                    'asset_account_id':
                    self.category_id.sale_income_account_id.id,
                    'partner_account_id':
                    self.category_id.sale_receivable_account_id.id,
                    'analytic_account_id':
                    self.category_id.sale_analytic_account_id.id,
                },
            }

    @api.multi
    def _get_move_line_vals(self, journal_type, amount_excl_tax, tax_amount,
                            taxes, accounts, default=None):
        self.ensure_one()
        lines = []
        if amount_excl_tax:
            debit, credit = abs(amount_excl_tax), 0.0
            if (amount_excl_tax < 0.0) ^ (
                    journal_type in ('sale', 'purchase_refund')):
                debit, credit = abs(credit), abs(debit)
            vals = (default or {}).copy()
            vals.update({
                'account_id': accounts['asset_account_id'],
                'debit': debit,
                'credit': credit,
                'asset_id': self.id,
                'analytic_account_id': accounts['analytic_account_id'],
            })
            lines.append(vals)
        if journal_type.startswith('purchase') and \
                self.invoice_line_ids and \
                self.invoice_line_ids[0].account_id != \
                self.category_id.asset_account_id:
            invoice_moves = self.invoice_line_ids.mapped('invoice_id.move_id')
            for move_line in self.account_move_line_ids:
                if not (move_line.debit or move_line.credit):
                    continue
                if move_line.move_id in invoice_moves:
                    vals = move_line.read([], load='_classic_write')[0]
                    vals['debit'], vals['credit'] = \
                        vals['credit'], vals['debit']
                    lines.append(vals)
        else:
            if taxes:
                lines.extend(
                    taxes._get_move_line_vals(
                        amount_excl_tax, journal_type,
                        accounts['analytic_account_id'], default))
            if amount_excl_tax + tax_amount:
                debit, credit = 0.0, abs(amount_excl_tax + tax_amount)
                if (amount_excl_tax + tax_amount < 0.0) ^ \
                        (journal_type in ('sale', 'purchase_refund')):
                    debit, credit = credit, debit
                vals = (default or {}).copy()
                vals.update({
                    'account_id': accounts['partner_account_id'],
                    'debit': debit,
                    'credit': credit,
                })
                lines.append(vals)
        return lines

    @api.multi
    def button_cancel_asset_purchase(self):
        return self.cancel_asset_purchase()

    @api.multi
    def cancel_asset_purchase(self):
        self._can_cancel_asset_purchase()
        if self.mapped('child_ids'):
            self.mapped('child_ids').cancel_asset_purchase()
        self.write({'state': 'cancel', 'invoice_line_ids': [(5,)]})
        self = self.with_context(force_account_move_date=fields.Date.today())
        for asset in self:
            asset.with_context(force_account_move_amount=None).create_move(
                'purchase', reverse=True)
            for depreciation_type in ('accounting', 'fiscal', 'exceptional'):
                force_account_move_amount = 0.0
                last_line = self.env['account.asset.depreciation.line']
                for line in asset[
                        '%s_depreciation_line_ids' % depreciation_type].\
                        filtered('is_posted').sorted('depreciation_date'):
                    value_field = 'depreciation_value'
                    if depreciation_type == 'fiscal':
                        value_field = 'accelerated_value'
                    force_account_move_amount += line[value_field]
                    last_line = line
                last_line.with_context(
                    force_account_move_amount=force_account_move_amount).\
                    post_depreciation_line(reverse=True)
            if not self.purchase_move_id:
                if self._changed_accounts():
                    origin_vals = asset.asset_history_ids.sorted(
                        'create_date')[0].read(load='_classic_write')[0]
                    asset.asset_history_ids.create(origin_vals)
        return True

    @api.one
    def _can_cancel_asset_purchase(self):
        if self.state == 'cancel':
            raise UserError(_('You cannot cancel a cancelled asset!'))
        if self.state == 'close':
            raise UserError(_('You cannot cancel a disposed asset!'))

    @api.multi
    def _changed_accounts(self):
        self.ensure_one()
        if self.asset_history_ids:
            old_category = self.asset_history_ids.sorted(
                'create_date')[0].category_id
            new_category = self.category_id
            if old_category != new_category:
                fields_to_read = [
                    'asset_account_id',
                    'accounting_depreciation_account_id',
                    'accounting_depreciation_expense_account_id',
                    'accounting_depreciation_income_account_id',
                    'exceptional_depreciation_account_id',
                    'exceptional_depreciation_expense_account_id',
                    'exceptional_depreciation_income_account_id',
                ]
                old_values = old_category.read(
                    fields_to_read, load='_classic_write')[0]
                new_values = new_category.read(
                    fields_to_read, load='_classic_write')[0]
                if self._get_changed_accounts(old_values, new_values):
                    return old_values, new_values
        return False

    @api.multi
    def button_validate(self):
        self.validate()
        return {'type': 'ir.actions.act_window_close'}

    @api.multi
    def validate(self):
        self._can_validate()
        self.compute_depreciation_board()
        return self.write({
            'state': 'open',
            'in_service_account_date': fields.Date.today(),
        })

    @api.one
    def _can_validate(self):
        if self.asset_in_progress:
            raise UserError(
                _('You cannot validate an asset in progress'))
        if not self.in_service_date:
            raise UserError(
                _('You cannot validate an asset without in-service date!'))
        if self.state == 'draft':
            raise UserError(
                _('Please confirm this asset before validating it!'))

    @api.multi
    def button_put_into_service(self):
        self.ensure_one()
        context = dict(self._context)
        context.update({
            'default_asset_id': self.id,
            'asset_validation': True,
        })
        return {
            'name': _('Asset Update'),
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'account.asset.history',
            'target': 'new',
            'context': context,
        }

    @api.multi
    def button_modify(self):
        self.ensure_one()
        context = dict(self._context)
        context['default_asset_id'] = self.id
        return {
            'name': _('Asset Update'),
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'account.asset.history',
            'target': 'new',
            'context': context,
        }

    @api.multi
    def button_split(self):
        self.ensure_one()
        context = dict(self._context)
        context.update({
            'default_asset_id': self.id,
            'default_purchase_value': self.purchase_value,
            'default_salvage_value': self.salvage_value,
            'default_quantity': self.quantity,
        })
        return {
            'name': _('Asset Split'),
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'account.asset.split_wizard',
            'target': 'new',
            'context': context,
        }

    @api.multi
    def button_sell(self):
        self.ensure_one()
        return {
            'name': _('Asset Sale/Scrapping'),
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'view_id': self.env.ref(
                'smile_account_asset.view_account_asset_asset_sale_form').id,
            'res_model': 'account.asset.asset',
            'res_id': self.id,
            'target': 'new',
            'context': self._context,
        }

    @api.multi
    def button_confirm_asset_sale(self):
        self.confirm_asset_sale()
        return {'type': 'ir.actions.act_window_close'}

    @api.multi
    def confirm_asset_sale(self):
        # TODO: manage multi-assets sale
        self._can_confirm_asset_sale()
        assets_to_recompute = self.filtered(
            lambda asset: not asset.accounting_depreciation_line_ids or
            max([line.depreciation_date
                 for line in asset.accounting_depreciation_line_ids]) >
            asset.sale_date
        )
        assets_to_recompute.compute_depreciation_board()
        for asset in self:
            asset.write(asset._get_sale_infos())
        self.write({'state': 'close'})
        return self.create_move('sale')

    @api.one
    def _can_confirm_asset_sale(self):
        if self.state not in ('confirm', 'open'):
            raise ValidationError(
                _('You cannot dispose a %s asset')
                % dict(ASSET_STATES)[self.state])
        if self.sale_type == 'scrapping' and self.sale_value:
            raise ValidationError(
                _('Scrapping value must be null'))

    @api.multi
    def _get_sale_infos(self):
        self.ensure_one()
        fiscal_book_value = self._get_fiscal_book_value()
        regularization_tax_amount = self._get_regularization_tax_amount()
        fiscal_sale_result = \
            self.sale_value - fiscal_book_value - regularization_tax_amount
        accumulated_amortization_value = \
            self.purchase_value - fiscal_book_value
        return {
            'tax_regularization': bool(regularization_tax_amount),
            'regularization_tax_amount': regularization_tax_amount,
            'sale_result': fiscal_sale_result,
            'sale_result_short_term':
                min(fiscal_sale_result, accumulated_amortization_value),
            'sale_result_long_term':
                fiscal_sale_result > accumulated_amortization_value and
                fiscal_sale_result - accumulated_amortization_value or 0.0,
            'fiscal_book_value': fiscal_book_value,
            'accumulated_amortization_value': accumulated_amortization_value,
            'sale_account_date':
                self.sale_account_date or fields.Date.today(),
        }

    @api.multi
    def _get_fiscal_book_value(self):
        # Fiscal Book Value = Gross Value - Sum of fiscal depreciations
        # (accounting_depreciation_value + fiscal_accelerated_value)
        self.ensure_one()
        fiscal_book_value = self.purchase_value
        if self.accounting_depreciation_line_ids:
            fiscal_book_value -= sum([
                depr.depreciation_value
                for depr in self.accounting_depreciation_line_ids], 0.0)
            if self.benefit_accelerated_depreciation and \
                    self.fiscal_depreciation_line_ids:
                fiscal_book_value -= sum([
                    depr.accelerated_value
                    for depr in self.fiscal_depreciation_line_ids], 0.0)
        return fiscal_book_value

    @api.multi
    def _get_regularization_tax_amount(self):
        rate = self._get_regularization_tax_rate()
        tax = self.category_id.tax_regularization_base == 'deducted' and \
            self.purchase_tax_amount or 0.0
        return tax * rate

    @api.multi
    def _get_regularization_tax_rate(self):
        self.ensure_one()
        regularization_tax_rate = 0.0
        if self.purchase_tax_amount:
            if self.category_id.tax_regularization_application == \
                    'with_sale_taxes':
                apply_regulatization = bool(self.sale_tax_ids)
            else:
                apply_regulatization = not self.sale_tax_ids
            regularization_period = self.category_id.tax_regularization_period
            if apply_regulatization and 0.0 <= \
                    int(time.strftime('%Y')) - self.purchase_date.year < \
                    regularization_period:
                depreciation_start_date = self.env[
                    'account.asset.depreciation.method']. \
                    get_depreciation_start_date(
                        self.accounting_method, self.purchase_date,
                        self.in_service_date)
                # TODO: manage fiscal years not starting on January 1rst
                remaining_years = regularization_period - \
                    (self.sale_date.year - depreciation_start_date.year + 1)
                if remaining_years > 0:
                    regularization_tax_rate = \
                        float(remaining_years) / regularization_period
        return regularization_tax_rate

    @api.multi
    def button_cancel_asset_sale(self):
        return self.cancel_asset_sale()

    @api.multi
    def cancel_asset_sale(self):
        self._can_cancel_asset_sale()
        self.mapped('child_ids').cancel_asset_sale
        self.filtered('is_out').create_output_moves(reverse=True)
        self.filtered('sale_value').create_move('sale', reverse=True)
        self.write({}.fromkeys(self._sale_fields, False))
        return self.validate()

    @api.one
    def _can_cancel_asset_sale(self):
        if self.state != 'close':
            raise UserError(
                _('You cannot cancel the disposal of an asset not disposed!'))

    @api.multi
    def button_output(self):
        return self.output()

    @api.multi
    def output(self):
        self._can_output()
        self.write({'is_out': True})
        return self.create_output_moves()

    @api.one
    def _can_output(self):
        if self.state != 'close':
            raise UserError(
                _('You cannot output an asset not already disposed!'))
        if self.is_out:
            raise UserError(
                _('You cannot output an asset already out!'))

    @api.multi
    def create_output_moves(self, reverse=False):
        # Constater les amortissements/dérogations non encore comptabilisés
        for asset in self:
            for line in asset.depreciation_line_ids:
                if not line.is_posted and \
                        (line.depreciation_type != 'fiscal' or
                         asset.benefit_accelerated_depreciation):
                    line.post_depreciation_line()
        context = dict(self._context)
        context['asset_output_msg'] = _('Asset Output%s, ') % \
            (reverse and _(' Cancellation') or '')
        for asset in self:
            context['force_account_move_date'] = max(
                asset.sale_date, fields.Date.today())
            # Si mise au rebut, annuler la VNC
            # en tant que dépréciation exceptionnelle
            context['asset_output'] = False
            if asset.company_id.convert_book_value_if_scrapping and \
                    asset.sale_type == 'scrapping':
                asset.env['account.asset.depreciation.line'].create({
                    'asset_id': asset.id,
                    'depreciation_type': 'exceptional',
                    'depreciation_date': context['force_account_move_date'],
                    'depreciation_value': asset.book_value,
                }).with_context(**context).post_depreciation_line()
            # Annuler les dépréciations (exceptional_value)
            context['asset_output'] = True
            exceptional_value = sum(
                asset.exceptional_depreciation_line_ids.filtered(
                    'is_posted').mapped('depreciation_value'))
            if exceptional_value:
                context['force_account_move_amount'] = exceptional_value * -1
                asset.exceptional_depreciation_line_ids.sorted(
                    'depreciation_date')[-1].with_context(
                        **context).post_depreciation_line()
            # Annuler les amortissements dérogatoires (accelerated_value)
            accelerated_value = sum(
                asset.fiscal_depreciation_line_ids.filtered(
                    'is_posted').mapped('accelerated_value'))
            if accelerated_value:
                context['force_account_move_amount'] = accelerated_value * -1
                asset.fiscal_depreciation_line_ids.sorted(
                    'depreciation_date')[-1].with_context(
                        **context).post_depreciation_line()
            # Annuler l'immobilisation et les amortissements comptables
            # (accounting_value), et constater la TVA à reverser
            asset.create_inventory_move(reverse)

    @api.multi
    def create_inventory_move(self, reverse=False):
        moves = self.env['account.move']
        for asset in self:
            vals = asset._get_inventory_move_vals(reverse)
            moves |= moves.create(vals)
        return moves.post()

    @api.multi
    def _get_inventory_move_vals(self, reverse=False):
        self.ensure_one()
        journal = self.category_id.asset_journal_id
        vals = {
            'name': journal.sequence_id.next_by_id(),
            'narration': _('Asset Output%s: %s') %
            (reverse and _(' Cancellation') or '', self.name),
            'ref': self.code,
            'date': fields.Date.today(),
            'journal_id': journal.id,
            'company_id': self.company_id.id,
        }
        default = vals.copy()
        default['currency_id'] = self.currency_id.id
        vals['line_ids'] = [
            (0, 0, x)
            for x in self._get_inventory_move_lines(default, reverse)]
        return vals

    @api.multi
    def _get_inventory_move_lines(self, default=None, reverse=False):
        self.ensure_one()
        posted_lines = self.accounting_depreciation_line_ids.filtered(
            'is_posted')
        accounting_value = sum(posted_lines.mapped('depreciation_value'))
        exceptional_amortization_value = \
            sum(posted_lines.mapped('book_value_wo_exceptional')) - \
            sum(posted_lines.mapped('book_value'))
        move_lines = [{
            'account_id': self.category_id.sale_expense_account_id.id,
            'debit': self.purchase_value - accounting_value -
            exceptional_amortization_value +
            self.regularization_tax_amount,
            'credit': 0.0,
            'asset_id': self.id,
            'analytic_account_id':
            self.category_id.sale_analytic_account_id.id,
        }, {
            'account_id':
            self.category_id.accounting_depreciation_account_id.id,
            'debit': accounting_value + exceptional_amortization_value,
            'credit': 0.0,
            'asset_id': self.id,
            'analytic_account_id':
            self.category_id.asset_analytic_account_id.id,
        }, {
            'account_id': self.category_id.asset_account_id.id,
            'debit': 0.0,
            'credit': self.purchase_value,
            'asset_id': self.id,
            'analytic_account_id':
            self.category_id.asset_analytic_account_id.id,
        }]
        if self.regularization_tax_amount:
            move_lines.extend(self._get_inventory_move_tax_lines())
        default = default or {}
        for index, line in enumerate(move_lines):
            if line['debit'] < 0 or line['credit'] < 0:
                line['debit'], line['credit'] = \
                    abs(line['credit']), abs(line['debit'])
            if (self.asset_type == 'purchase_refund') ^ reverse:
                line['debit'], line['credit'] = line['credit'], line['debit']
            line.update(default or {})
        return move_lines

    @api.multi
    def _get_inventory_move_tax_lines(self):
        self.ensure_one()
        tax_amounts = {}
        taxes = self.purchase_tax_ids.compute_all(self.purchase_value)['taxes']
        for tax in taxes:
            tax_amounts.setdefault(tax['account_collected_id'], 0.0)
            tax_amounts[tax['account_collected_id']] += tax['amount']
        regularization_rate = self._get_regularization_tax_rate()
        return [{
            'account_id': tax_account_id,
            'debit': 0.0,
            'credit': tax_amount * regularization_rate,
            'analytic_account_id':
            self.category_id.asset_analytic_account_id.id,
        } for tax_account_id, tax_amount in tax_amounts.items()]

    @api.model
    def change_accounts(self, relation, old_values, new_values):
        if self._context.get('ignore_change_accounts'):
            return True
        accounts_by_group = self._get_changed_accounts(old_values, new_values)
        relation_model, relation_id = relation.split(',')
        relation_id = int(relation_id)
        if relation_model == 'res.company':
            relation_field = 'company_id'
        elif relation_model == 'account.asset.category':
            relation_field = 'category_id'
        else:
            relation_field = 'id'
        for group in accounts_by_group:
            old_accounts, new_accounts = self._get_group_accounts(
                group, old_values, new_values)
            if group == 'purchase':
                domain = [(relation_field, '=', relation_id)]
                if relation_model != 'account.asset.asset':
                    domain += [('state', 'in', ['confirm', 'open'])]
                assets = self.search(domain)
                assets._transfer_from_accounts_to_others(
                    group, old_accounts, new_accounts)
            else:
                depreciation_type = group.replace('_depreciation', '')
                if group == "exceptional_amortization":
                    depreciation_type = 'accounting'
                domain = [
                    (relation_field == 'id' and 'asset_id' or relation_field,
                     '=', relation_id),
                    ('depreciation_type', '=', depreciation_type),
                    ('is_posted', '=', True),
                ]
                if depreciation_type == 'fiscal':
                    domain.append(
                        ('benefit_accelerated_depreciation', '=', True))
                depreciation_lines = self.env[
                    'account.asset.depreciation.line'].search(domain)
                depreciation_lines._transfer_from_accounts_to_others(
                    group, old_accounts, new_accounts)
        return True

    @api.model
    def _get_changed_accounts(self, old_values, new_values):
        assert sorted(old_values.keys()) == sorted(new_values.keys()), \
            "old_values and new_values must have the same keys!"
        accounts_by_group = {}
        for account in new_values:
            if account in ACCOUNT_GROUPS and old_values[account] and \
                    old_values[account] != new_values[account]:
                group = ACCOUNT_GROUPS[account]
                accounts_by_group.setdefault(group, {})
                accounts_by_group[group][account] = new_values[account]
        return accounts_by_group

    @api.model
    def _get_group_accounts(self, group, old_values, new_values):
        old_accounts, new_accounts = {}, {}
        for account in ACCOUNT_GROUPS:
            if ACCOUNT_GROUPS[account] == group and account in old_values:
                # old_values[account] != new_values[account] is implicit,
                # see _get_changed_accounts
                old_accounts[account] = old_values[account]
                new_accounts[account] = new_values[account]
        return old_accounts, new_accounts

    @api.multi
    def _transfer_from_accounts_to_others(
            self, accounts_group, old_accounts, new_accounts):
        moves = self.env['account.move']
        if accounts_group == 'purchase':
            analytic_field = 'asset_analytic_account_id'
        else:
            analytic_field = 'sale_analytic_account_id'
        self = self.with_context(force_account_move_date=fields.Date.today())
        for asset in self:
            vals = asset._get_move_vals(accounts_group)
            new_line_vals = []
            for i, j, line_vals in vals['line_ids']:
                for account, group in ACCOUNT_GROUPS.items():
                    if group != accounts_group or \
                            account not in old_accounts or \
                            'analytic' in account:
                        continue
                    if line_vals['account_id'] == old_accounts[account] or \
                            (analytic_field in old_accounts and
                             analytic_field in line_vals):
                        transfer_vals = line_vals.copy()
                        if account in new_accounts:
                            transfer_vals['account_id'] = new_accounts[account]
                        if analytic_field in new_accounts:
                            transfer_vals['analytic_account_id'] = \
                                new_accounts[analytic_field]
                        line_vals['debit'], line_vals['credit'] = \
                            line_vals['credit'], line_vals['debit']
                        new_line_vals.extend(
                            [(0, 0, transfer_vals), (0, 0, line_vals)])
                        break
            if new_line_vals:
                vals['line_ids'] = new_line_vals
                moves |= moves.create(vals)
        return moves.post() if moves else True

    @api.multi
    def _get_last_depreciation(self, depreciation_date, is_posted=True):
        self.ensure_one()
        return self.env['account.asset.depreciation.line'].search([
            ('asset_id', '=', self.id),
            ('depreciation_type', '=', 'accounting'),
            ('depreciation_date', '<=', depreciation_date),
            ('is_posted', '=', is_posted),
        ], limit=1, order='depreciation_date desc')
