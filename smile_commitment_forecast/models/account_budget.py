# -*- coding: utf-8 -*-
# (C) 2018 Smile (<http://www.smile.fr>)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import api, fields, models


class BudgetLine(models.Model):
    _inherit = 'crossovered.budget.lines'

    @api.model_cr
    def init(self):
        super(BudgetLine, self).init()
        self._fields_to_compute += ['forecast_commitment_amount',
                                    'forecast_available_amount']

    forecast_commitment_amount = fields.Float(
        digits=0, compute="_compute_practical_amount")
    forecast_available_amount = fields.Float(
        digits=0, compute="_compute_practical_amount")

    @api.multi
    def _compute_practical_amount(self):
        super(BudgetLine, self)._compute_practical_amount()
        for line in self:
            acc_ids = line.general_budget_id.account_ids.ids
            date_to = self.env.context.get('wizard_date_to') or \
                line.date_to
            date_from = self.env.context.get('wizard_date_from') or \
                line.date_from
            today = fields.Date.today()
            forecast_commitment_amount = 0.0  # TODO: check if it's a good fix
            if line.analytic_account_id.id and date_to >= today:
                date_from = min(date_from, today)
                params = (line.analytic_account_id.id,
                          date_from, date_to, acc_ids,)
                self.env.cr.execute(
                    self._get_sql_query(forecast=True) +
                    "AND general_account_id=ANY(%s)", params)
                forecast_commitment_amount = self.env.cr.fetchone()[0] or 0.0
            line.forecast_commitment_amount = forecast_commitment_amount + \
                line.commitment_amount
            line.forecast_available_amount = line.planned_amount - \
                line.forecast_commitment_amount

    @api.model
    def _get_sql_query(self, forecast=False):
        return super(BudgetLine, self)._get_sql_query() + \
            " AND forecast IS %sTRUE " % ('' if forecast else 'NOT ')
