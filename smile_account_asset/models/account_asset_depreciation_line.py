# -*- coding: utf-8 -*-
# (C) 2019 Smile (<http://www.smile.fr>)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from dateutil.relativedelta import relativedelta

from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError

from .account_asset_asset import ACCOUNT_GROUPS


class AccountAssetDepreciationLine(models.Model):
    _name = 'account.asset.depreciation.line'
    _description = 'Asset Depreciation Line'
    _order = 'depreciation_date'

    @api.model_cr
    def init(self):
        super(AccountAssetDepreciationLine, self).init()
        self._cr.execute("""
            SELECT * FROM pg_proc WHERE proname = 'last' AND proisagg;""")
        if not self._cr.fetchall():
            self._cr.execute("""
-- Create a function that always returns the last non-NULL item
CREATE OR REPLACE FUNCTION public.last_agg ( anyelement, anyelement )
RETURNS anyelement LANGUAGE sql IMMUTABLE STRICT AS $$
        SELECT $2;
$$;

-- And then wrap an aggregate around it
CREATE AGGREGATE public.last (
        sfunc    = public.last_agg,
        basetype = anyelement,
        stype    = anyelement
);""")

    asset_id = fields.Many2one(
        'account.asset.asset', 'Asset', required=True, ondelete='cascade',
        index=True, auto_join=True)
    depreciation_type = fields.Selection([
        ('accounting', 'Accounting'),
        ('fiscal', 'Fiscal'),
        ('exceptional', 'Exceptional'),
    ], 'Type', required=True, index=True, default='exceptional')
    depreciation_date = fields.Date(
        'Date', required=True, default=fields.Date.context_today)
    active = fields.Boolean(default=True)
    company_id = fields.Many2one(
        related='asset_id.company_id', store=True,
        readonly=True, index=True)
    currency_id = fields.Many2one(
        related='asset_id.currency_id', store=True, readonly=True)
    category_id = fields.Many2one(
        related='asset_id.category_id', store=True, readonly=True)
    state = fields.Selection(
        related='asset_id.state', store=True, readonly=True)
    asset_type = fields.Selection(
        related='asset_id.asset_type', store=True, readonly=True)
    benefit_accelerated_depreciation = fields.Boolean(
        related='asset_id.benefit_accelerated_depreciation',
        store=True, readonly=True)
    base_value = fields.Monetary('Base Amount', readonly=True)
    previous_years_accumulated_value = fields.Monetary(
        'Previous Years Accumulated Depreciation',
        readonly=True, group_operator="last")
    previous_years_accumulated_value_sign = fields.Monetary(
        'Previous Years Accumulated Depreciation',
        compute='_get_accumulated_value_sign', store=True)
    current_year_accumulated_value = fields.Monetary(
        'Current Year Accumulated Depreciation',
        readonly=True, group_operator="last")
    current_year_accumulated_value_sign = fields.Monetary(
        'Current Year Accumulated Depreciation',
        compute='_get_accumulated_value_sign', store=True)
    depreciation_value = fields.Monetary('Depreciation')
    depreciation_value_sign = fields.Monetary(
        'Depreciation', compute='_get_accumulated_value_sign', store=True)
    accumulated_value = fields.Monetary(
        'Accumulated Depreciation', readonly=True)
    exceptional_value = fields.Monetary(
        'Exceptional Depreciation', readonly=True)
    exceptional_value_sign = fields.Monetary(
        'Exceptional Depreciation',
        compute='_get_accumulated_value_sign', store=True)
    book_value = fields.Monetary('Book value', readonly=True)
    book_value_sign = fields.Monetary(
        'Book value', compute='_get_accumulated_value_sign', store=True)
    book_value_wo_exceptional = fields.Monetary(
        'Book value at end without exceptional', readonly=True)
    move_id = fields.Many2one(
        'account.move', 'Depreciation Entry',
        readonly=True, ondelete='restrict')
    accounting_value = fields.Monetary(
        'Accounting Depreciation',
        compute='_get_depreciation_values', store=True)
    accelerated_value = fields.Monetary(
        'Accelerated Depreciation',
        compute='_get_depreciation_values', store=True)
    # TODO: store it not recomputed after line posting
    purchase_value = fields.Monetary(
        'Gross Value', related='asset_id.purchase_value',
        store=True, readonly=True)
    purchase_value_sign = fields.Monetary(
        'Gross Value', compute='_get_accumulated_value_sign', store=True)
    salvage_value = fields.Monetary(
        'Salvage Value', related='asset_id.salvage_value',
        store=True, readonly=True)
    salvage_value_sign = fields.Monetary(
        'Salvage Value', compute='_get_accumulated_value_sign', store=True)
    year = fields.Char("Year", compute='_get_year', store=True)
    account_id = fields.Many2one(
        'account.account', 'Account', compute='_get_account', store=True)
    is_posted = fields.Boolean(
        'Posted Depreciation',
        compute='_get_is_posted', inverse='_set_is_posted', store=True)
    is_posted_forced = fields.Boolean(readonly=True)
    is_manual = fields.Boolean(
        'Manual Depreciation', compute='_get_is_manual', store=True)

    @api.one
    @api.depends('previous_years_accumulated_value',
                 'current_year_accumulated_value',
                 'depreciation_value', 'book_value',
                 'purchase_value', 'exceptional_value',
                 'salvage_value', 'asset_id.asset_type')
    def _get_accumulated_value_sign(self):
        sign = self.asset_id.asset_type == 'purchase_refund' and -1 or 1
        self.previous_years_accumulated_value_sign = \
            self.previous_years_accumulated_value * sign
        self.current_year_accumulated_value_sign = \
            self.current_year_accumulated_value * sign
        self.depreciation_value_sign = self.depreciation_value * sign
        self.book_value_sign = self.book_value * sign
        self.purchase_value_sign = self.purchase_value * sign
        self.exceptional_value_sign = self.exceptional_value * sign
        self.salvage_value_sign = self.salvage_value * sign

    @api.one
    @api.depends('depreciation_date', 'company_id.fiscalyear_start_day')
    def _get_year(self):
        self.year = self.depreciation_date.strftime('%Y')
        if self.depreciation_date.strftime('%m-%d') < self.company_id. \
                fiscalyear_start_day:
            self.year = str(int(self.year) - 1)

    @api.one
    @api.depends('depreciation_type',
                 'category_id.accounting_depreciation_account_id',
                 'category_id.exceptional_depreciation_account_id',
                 'company_id.fiscal_depreciation_account_id')
    def _get_account(self):
        if self.depreciation_type == 'fiscal':
            self.account_id = self.company_id.fiscal_depreciation_account_id
        else:
            self.account_id = self.category_id['%s_depreciation_account_id'
                                               % self.depreciation_type]

    @api.one
    @api.depends('is_posted_forced', 'move_id')
    def _get_is_posted(self):
        self.is_posted = self.is_posted_forced or bool(self.move_id)

    @api.one
    def _set_is_posted(self):
        self.is_posted_forced = self.is_posted

    @api.one
    @api.depends('depreciation_type',
                 'asset_id.accounting_method',
                 'asset_id.fiscal_method')
    def _get_is_manual(self):
        if self.depreciation_type == 'exceptional':
            self.is_manual = True
        else:
            self.is_manual = self.asset_id[
                '%s_method' % self.depreciation_type] == 'manual'

    @api.one
    @api.depends('depreciation_date', 'depreciation_value')
    def _get_depreciation_values(self):
        if self.depreciation_type == 'fiscal':
            self.accounting_value = self.asset_id.depreciation_line_ids. \
                filtered(
                    lambda line: line.depreciation_type == 'accounting' and
                    line.depreciation_date == self.depreciation_date
                ).depreciation_value
            self.accelerated_value = self.depreciation_value - \
                self.accounting_value

    @api.one
    @api.constrains('depreciation_value', 'book_value',
                    'book_value_wo_exceptional')
    def _check_constraints(self):
        if self.depreciation_value > self.asset_id.purchase_value:
            raise ValidationError(_(
                'Depreciation value cannot be bigger than gross value!'))
        if self.book_value > self.book_value_wo_exceptional:
            raise ValidationError(_(
                'Book value with exceptional depreciations '
                'cannot be superior to book value '
                'without exceptional depreciations, '
                'nor inferior to salvage value!'))

    @api.multi
    def button_validate_exceptional_depreciation(self):
        self.validate_exceptional_depreciation()
        return {'type': 'ir.actions.act_window_close'}

    @api.multi
    def validate_exceptional_depreciation(self):
        self.mapped('asset_id').compute_depreciation_board()
        return self.post_depreciation_line()

    @api.multi
    def write(self, vals):
        if 'active' in vals and not vals.get('active'):
            self._reverse_move(vals)
        return super(AccountAssetDepreciationLine, self).write(vals)

    @api.multi
    def _reverse_move(self, vals):
        lines_to_reverse = self.browse()
        if vals.get('is_posted') or vals.get('move_id') or \
                vals.get('is_posted_forced'):
            lines_to_reverse = self
        elif 'is_posted' not in vals and 'move_id' not in vals and \
                'is_posted_forced' not in vals:
            lines_to_reverse = self.filtered(lambda line: line.is_posted)
        if lines_to_reverse:
            lines_to_reverse.with_context(daily_amortization=True). \
                post_depreciation_line(reverse=True)

    @api.multi
    def post_depreciation_line(self, reverse=False):
        if not self:
            return True
        moves = self.env['account.move']
        for line in self:
            if (not line.depreciation_value or line.is_posted) and \
                    not reverse and not self._context.get('asset_output'):
                continue
            if line.depreciation_type == 'fiscal' and \
                    not line.asset_id.benefit_accelerated_depreciation:
                continue
            vals = line._get_move_vals(reverse)
            if vals['line_ids']:
                move = moves.create(vals)
                moves |= move
                if not self._context.get('asset_output'):
                    if not line.move_id:
                        line.move_id = move
                    if not reverse and line.depreciation_type == 'accounting' \
                            and line.book_value != \
                            line.book_value_wo_exceptional:
                        vals = line._get_move_vals(
                            reverse, 'from_depreciation')
                        if vals['line_ids']:
                            moves.create(vals)
                        vals = line._get_move_vals(
                            reverse, 'to_exceptional_amortization')
                        if vals['line_ids']:
                            moves.create(vals)
        return moves.post()

    @api.multi
    def _get_move_vals(self, reverse=False, transfer=None):
        self.ensure_one()
        move_date = self.depreciation_date
        if self._context.get('force_account_move_date'):
            move_date = self._context['force_account_move_date']
        elif self.asset_id.in_service_account_date and \
                self.depreciation_date < self.asset_id.in_service_account_date:
            move_date = fields.Date.to_string(fields.Date.from_string(
                self.asset_id.in_service_account_date) +
                relativedelta(day=1, months=1) + relativedelta(days=-1))
        msg = _('%s Amortization' % self.depreciation_type.capitalize())
        if transfer:
            msg = _('Exceptional Amortization')
        narration = '%s%s: %s - %s' % (
            self._context.get('asset_output_msg', ''), msg,
            self.asset_id.name, self.depreciation_date)
        journal = self.category_id.depreciation_journal_id or \
            self.category_id.asset_journal_id
        vals = {
            'name': journal.sequence_id.
            with_context(ir_sequence_date=move_date).next_by_id(),
            'narration': narration,
            'ref': self.asset_id.code,
            'date': move_date,
            'journal_id': journal.id,
            'company_id': self.company_id.id,
        }
        vals['line_ids'] = [
            (0, 0, x)
            for x in self._get_move_line_vals(vals.copy(), reverse, transfer)]
        return vals

    @api.multi
    def _get_move_line_vals(self, default=None, reverse=False, transfer=None):
        self.ensure_one()
        amount = self.depreciation_value
        main_related_object = self.category_id
        second_related_object = None
        depreciation_type = '%s_depreciation' % self.depreciation_type
        if transfer:
            depreciation_type = 'exceptional_amortization'
        account_field = '%s_account_id' % depreciation_type
        expense_account_field = '%s_expense_account_id' % \
            depreciation_type
        income_account_field = '%s_income_account_id' % \
            depreciation_type
        if self.depreciation_type == 'fiscal':
            if not self.company_id[expense_account_field] or \
                    not self.company_id[income_account_field] or \
                    not self.company_id[account_field]:
                raise UserError(
                    _('Please indicate fiscal amortization '
                        'accounts in company form!'))
            amount = self.accelerated_value
            main_related_object = self.company_id
        if transfer:
            if not self.company_id[expense_account_field] or \
                    not self.company_id[income_account_field]:
                raise UserError(
                    _('Please indicate exceptional amortization '
                        'accounts in company form!'))
            # INFO: always >= 0.0 by defintion, see French law
            amount = self.book_value_wo_exceptional - self.book_value
            second_related_object = self.company_id
            if transfer == 'from_depreciation':
                account_field = 'exceptional_depreciation_account_id'
            elif transfer == 'to_exceptional_amortization':
                amount *= -1.0
                account_field = 'accounting_depreciation_account_id'
        if self._context.get('force_account_move_amount'):
            amount = self._context['force_account_move_amount']
        if not amount:
            return []
        debit, credit = 0.0, abs(amount)
        if (self.asset_type == 'purchase_refund') ^ (
                (amount < 0.0) ^ bool(reverse)):
            debit, credit = abs(credit), abs(debit)
        default = default or {}
        default.update({
            'partner_id': self.asset_id.supplier_id.id,
            'currency_id': self.currency_id.id,
        })
        depreciation_line_vals = default.copy()
        depreciation_line_vals.update({
            'debit': debit,
            'credit': credit,
            'account_id': main_related_object[account_field].id,
            'analytic_account_id':
                self.category_id.asset_analytic_account_id.id,
            'asset_id': self.asset_id.id,
        })
        expense_or_income_line_vals = default.copy()
        related_object = second_related_object or main_related_object
        account_field = amount > 0 and expense_account_field or \
            income_account_field
        expense_or_income_line_vals.update({
            'debit': credit,
            'credit': debit,
            'account_id': related_object[account_field].id,
        })
        return [depreciation_line_vals, expense_or_income_line_vals]

    @api.multi
    def _transfer_from_accounts_to_others(
            self, accounts_group, old_accounts, new_accounts):
        moves = self.env['account.move']
        last_depreciation_line_by_asset = {}
        for depreciation_line in self:
            amount_field = 'depreciation_value'
            if depreciation_line.depreciation_type == 'fiscal':
                amount_field = 'accelerated_value'
            last_depreciation_line_by_asset[depreciation_line.asset_id] = \
                depreciation_line, depreciation_line[amount_field]
        context = {'force_account_move_date': fields.Date.today()}
        for depreciation_line, amount in \
                last_depreciation_line_by_asset.values():
            context['force_account_move_amount'] = amount
            transfer_groups = ['']
            if accounts_group == 'exceptional_amortization':
                transfer_groups = ['from_depreciation',
                                   'to_exceptional_amortization']
            for transfer in transfer_groups:
                vals = depreciation_line.with_context(**context). \
                    _get_move_vals(transfer=transfer)
                new_line_vals = []
                for i, j, line_vals in vals['line_ids']:
                    for account, group in ACCOUNT_GROUPS.items():
                        if group == accounts_group and \
                                account in old_accounts and \
                                line_vals['account_id'] == \
                                old_accounts[account]:
                            transfer_vals = line_vals.copy()
                            transfer_vals['account_id'] = new_accounts[account]
                            line_vals['debit'], line_vals['credit'] = \
                                line_vals['credit'], line_vals['debit']
                            new_line_vals.extend(
                                [(0, 0, transfer_vals), (0, 0, line_vals)])
                            break
                vals['line_ids'] = new_line_vals
                moves |= moves.create(vals)
        return moves.post() if moves else True

    @api.model
    def _search(self, args, offset=0, limit=None, order=None, count=False,
                access_rights_uid=None):
        args = args or []
        first_day_of_current_month = fields.Date.from_string(
            fields.Date.today()) + relativedelta(day=1)
        if self._context.get('search_in_current_month'):
            first_day_of_next_month = first_day_of_current_month + \
                relativedelta(months=1)
            args = [
                '&',
                ('depreciation_date', '>=', fields.Date.to_string(
                    first_day_of_current_month)),
                ('depreciation_date', '<', fields.Date.to_string(
                    first_day_of_next_month)),
            ] + args
        if self._context.get('search_in_three_months'):
            first_day_of_three_months_before = first_day_of_current_month - \
                relativedelta(months=3)
            args = [
                '&',
                ('depreciation_date', '>=', fields.Date.to_string(
                    first_day_of_three_months_before)),
                ('depreciation_date', '<', fields.Date.to_string(
                    first_day_of_current_month)),
            ] + args
        return super(AccountAssetDepreciationLine, self)._search(
            args, offset, limit, order, count, access_rights_uid)

    @api.model
    @api.returns('self', lambda records: records.ids)
    def bulk_create(self, vals_list):
        if not vals_list:
            return self.browse()
        context = dict(self._context)
        if not self._context.get('force_store_function'):
            # 'force_store_function' useful if model has workflow
            # with transition condition
            # based on function/compute fields
            context['no_store_function'] = True
            context['recompute'] = False
        context['no_validate'] = True
        context['defer_parent_store_computation'] = True
        if not isinstance(vals_list, list):
            vals_list = [vals_list]
        records = self.browse()
        for vals in vals_list:
            records |= self.with_context(**context).create(vals)
        if not self._context.get('force_store_function'):
            records.modified(self._fields)
            self.recompute()
        self._parent_store_compute()
        records._validate_fields(vals_list[0])
        return records
