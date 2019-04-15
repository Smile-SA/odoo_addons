# -*- coding: utf-8 -*-
# (C) 2018 Smile (<http://www.smile.fr>)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import models, api, _


class AccountBankStatementLine(models.Model):
    _inherit = 'account.bank.statement.line'

    @api.multi
    def button_reconcile_line(self):
        """
            Button to reconcile one bank statement line
        """
        self.ensure_one()
        self = self.with_context(statement_ids=[self.statement_id.id], reconciliation_by_line_id=self.id)
        return {
            'name': _('Bank statement reconciliation for %s') % (self.partner_id.name or self.name),
            'type': 'ir.actions.client',
            'tag': 'bank_statement_reconciliation_byline_view',
            'context': self._context,
            'target': 'new',
        }
