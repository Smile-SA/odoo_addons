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

from openerp import api, models, _
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
        res = super(PurchaseOrderLine, self).action_confirm()
        self._create_analytic_line()
        return res
