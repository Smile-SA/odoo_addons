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

from openerp import models, fields, api, exceptions
from openerp.tools.translate import _


class WizardAccountInvoiceRejectionCause(models.TransientModel):
    """Invoice Rejection Cause"""
    _name = "account.invoice.rejection.cause"

    invoice_id = fields.Many2one('account.invoice', string='Account invoice', required=True, readonly=True)
    rejection_cause_id = fields.Many2one('rejection.cause', 'Rejection cause', required=True)
    note = fields.Text(required=True)

    @api.multi
    def button_reject(self):
        self.ensure_one()
        if not self.invoice_id:
            raise exceptions.Warning(_('Required data!'), _("""Invoice is required!"""))
        if not self.rejection_cause_id:
            raise exceptions.Warning(_('Required data!'), _("""Rejection cause is required!"""))
        if not self.note:
            raise exceptions.Warning(_('Required data!'), _("""Note is required!"""))
        return self.invoice_id.no_bap_invoice(self.rejection_cause_id.id, self.note)
