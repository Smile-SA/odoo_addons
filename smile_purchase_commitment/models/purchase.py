# -*- encoding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2014 Smile (<http://www.smile.fr>). All Rights Reserved
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

from openerp import api, fields, models, _
from openerp.exceptions import Warning


class PurchaseOrderLine(models.Model):
    _inherit = 'purchase.order.line'

    def _prepare_analytic_line(self):
        general_account_id = self.pool['purchase.order']._choose_account_from_po_line(self._cr, self._uid, self, self._context)
        general_journal = self.env['account.journal'].search([('type', '=', 'purchase'), ('company_id', '=', self.company_id.id)], limit=1)
        if not general_journal:
            raise Warning(_('Define an accounting journal for purchase'))
        if not general_journal.commitment_analytic_journal_id:
            raise Warning(_("No analytic journal for commitments defined on the accounting journal '%s'") % general_journal.name)
        return {
            'name': self.name,
            'product_id': self.product_id.id,
            'account_id': self.account_analytic_id.id,
            'unit_amount': self.product_qty,
            'product_uom_id': self.product_uom.id,
            'amount': self.price_subtotal,
            'general_account_id': general_account_id,
            'journal_id': general_journal.commitment_analytic_journal_id.id,
            'ref': self.order_id.name,
            'user_id': self._uid,
        }

    @api.one
    def _create_analytic_line(self):
        if self.account_analytic_id:
            vals = self._prepare_analytic_line()
            self.env['account.analytic.line'].create(vals)

    @api.multi
    def action_confirm(self):
        for order in [l.order_id for l in self]:
            order.check_budget()
        res = super(PurchaseOrderLine, self).action_confirm()
        self._create_analytic_line()
        return res


class PurchaseOrder(models.Model):
    _inherit = 'purchase.order'

    @api.multi
    def _get_amounts_by_budget_line(self):
        res = {}
        cr, uid, context = self.env.args
        budget_line_obj = self.env['crossovered.budget.lines']
        for line in self.order_line:
            general_account_id = self.pool['purchase.order']._choose_account_from_po_line(cr, uid, line, context)
            budget_lines = budget_line_obj.search([
                ('analytic_account_id', '=', line.account_analytic_id.id),
                ('general_budget_id.account_ids', 'in', general_account_id),
                ('date_from', '<=', fields.Date.today()),
                ('date_to', '>=', fields.Date.today()),
            ], limit=1)
            if budget_lines:
                res.setdefault(budget_lines[0], 0.0)
                res[budget_lines[0]] += line.price_subtotal
        return res

    @api.multi
    def _check_budget_available(self):
        for budget_line, amount in self._get_amounts_by_budget_line().iteritems():
            if budget_line.available_amount - amount < 0.0:
                raise Warning(_("Available is exceeded for the budget line '%s'")
                              % budget_line.analytic_account_id.display_name)

    @api.multi
    def _get_amounts_by_budget_pos(self):
        res = {}
        for budget_line, amount in self._get_amounts_by_budget_line().iteritems():
            res.setdefault(budget_line.general_budget_id.id, 0.0)
            res[budget_line.general_budget_id.id] += amount
        return res

    @api.multi
    def _check_commitment_limit(self):
        warning_msg = _("You are authorized to confirm this order.\nAmount for '%s' exceeds your commitment authorization")
        for budget_pos_id, amount in self._get_amounts_by_budget_pos().iteritems():
            limits = [limit for limit in self.env.user.commitment_limit_ids if limit.budget_pos_id.id == budget_pos_id]
            if limits:
                if limits[0].amount_limit < amount:
                    raise Warning(warning_msg % limit.budget_pos_id.display_name)
            elif self.env.user.commitment_global_limit < amount:
                raise Warning(warning_msg % limit.budget_pos_id.display_name)

    @api.one
    def check_budget(self):
        self._check_budget_available()
        self._check_commitment_limit()
        return True
