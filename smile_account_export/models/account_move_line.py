# -*- coding: utf-8 -*-

from odoo import api, fields, models


class AccountMoveLine(models.Model):
    _inherit = 'account.move.line'

    exported = fields.Boolean(
        compute='_get_export_infos', search='_search_exported',
        groups="account.group_account_user")
    first_generation_date = fields.Date(
        compute='_get_export_infos', search='_search_first_generation_date',
        groups="account.group_account_user")
    last_generation_date = fields.Date(
        compute='_get_export_infos', search='_search_last_generation_date',
        groups="account.group_account_user")

    @api.multi
    def _get_export_infos(self):
        all_exports = self.env['account.export'].search([
            ('state', '=', 'done'),
        ])
        for aml in self:
            exports = all_exports.filtered(
                lambda exp: ',%s,' % aml.id in exp.record_ids)
            aml.exported = bool(exports)
            generation_dates = exports.mapped('generation_date')
            if generation_dates:
                aml.first_generation_date = min(generation_dates)
                aml.last_generation_date = max(generation_dates)
            else:
                aml.first_generation_date = False
                aml.last_generation_date = False

    @api.model
    def _search_exported(self, operator, value):
        exports = self.env['account.export'].search([])
        ids = exports.mapped('account_move_line_ids').ids
        op = (operator == '!=') ^ (not value) and 'not in' or 'in'
        return [('id', op, ids)]

    @api.model
    def _search_generation_date(self, operator, value, exclude):
        exports = self.env['account.export'].search([
            ('generation_date', operator, value),
        ])
        ids = exports.mapped('account_move_line_ids').ids
        if exclude:
            inv_ops = {'>': '<=', '>=': '<', '<': '>=', '<=': '>',
                       '=': '!=', '!=': '=', '<>': '='}
            exports = self.env['account.export'].search([
                ('generation_date', inv_ops[operator], value),
            ])
            ids -= exports.mapped('account_move_line_ids').ids
        return [('id', 'in', ids)]

    @api.model
    def _search_first_generation_date(self, operator, value):
        return self._search_generation_date(operator, value, '>' in operator)

    @api.model
    def _search_last_generation_date(self, operator, value):
        return self._search_generation_date(operator, value, '<' in operator)
