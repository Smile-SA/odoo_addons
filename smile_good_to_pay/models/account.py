# -*- encoding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2015 Smile (<http://www.smile.fr>). All Rights Reserved
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

import time
from lxml import etree

from openerp import models, fields, api, exceptions
from openerp.tools.translate import _


class RejectionCause(models.Model):
    _name = "rejection.cause"
    _description = "Rejection cause"

    name = fields.Char('Name', size=256, required=True)
    note = fields.Text('Note', size=512)

    _sql_constraints = [
        ('uniq_name', 'UNIQUE(name)', 'The name must be unique!'),
    ]


class AccountInvoice(models.Model):
    _inherit = 'account.invoice'

    @api.model
    def _setup_fields(self):
        super(AccountInvoice, self)._setup_fields()
        states = self._fields['state'].selection
        if 'wait' not in dict(self._fields['state'].selection):
            states = states[:len(states) - 3] + [('wait', 'Wait'), ('no_bap', 'NO BAP')] + states[-3:]
        self._fields['state'].selection = states

    reception_date = fields.Date(string='Reception date', copy=False)
    accounting_date = fields.Date(string='Accounting date', readonly=True, copy=False)
    approval_date = fields.Date(string='Approval date', readonly=True, copy=False)
    approval_user_id = fields.Many2one('res.users', string='Approval user', default=lambda self: self.env.user)
    rejection_cause_id = fields.Many2one('rejection.cause', 'Rejection cause', copy=False, readonly=True)
    rejection_note = fields.Text('Reject Note', copy=False, readonly=True)
    rejection_date = fields.Date(string='Rejection date', copy=False, readonly=True)

    @api.multi
    def invoice_validate(self):
        """
        Override :
            1. State ===> wait.(when invoice type == 'in_invoice')
            2. Update accounting date.
        """
        res = super(AccountInvoice, self).invoice_validate()
        for invoice in self:
            if invoice.type in ('in_invoice', 'in_refund'):
                invoice.write({'state': 'wait', 'accounting_date': time.strftime('%Y-%m-%d')})
        return res

    @api.multi
    def button_open_invoice(self):
        """
        Open invoice:
            1.State ===> open.
            2. Update approval date.
        """
        return self.write({'state': 'open', 'approval_date': time.strftime('%Y-%m-%d')})

    @api.multi
    def button_no_bap_invoice_wizard(self):
        self.ensure_one()
        return {
            'name': _('Rejection cause'),
            'view_type': 'form',
            'view_mode': 'form',
            'view_id': False,
            'res_model': 'account.invoice.rejection.cause',
            'domain': [],
            'context': dict(self._context, default_invoice_id=self.id),
            'type': 'ir.actions.act_window',
            'target': 'new',
            'res_id': False,
        }

    @api.multi
    def no_bap_invoice(self, rejection_cause_id, note):
        self.ensure_one()
        return self.write({'state': 'no_bap', 'rejection_cause_id': rejection_cause_id,
                           'rejection_note': note, 'rejection_date': time.strftime('%Y-%m-%d')})

    @api.multi
    def action_date_assign(self):
        """
        Override :
            1.Check amount limit(when invoice type == 'in_invoice')
        """
        for invoice in self:
            if invoice.type in ('in_invoice', 'in_refund') and invoice.amount_untaxed > self.env.user.amount_limit:
                raise exceptions.Warning(_("Amount!"), _("You are not authorized to validate this invoice !"))
        return super(AccountInvoice, self).action_date_assign()

    @api.model
    def fields_view_get(self, view_id=None, view_type=False, toolbar=False, submenu=False):
        """
        Override: Invisible approval_user_id if invoice type != 'in_invoice'
        """
        res = super(AccountInvoice, self).fields_view_get(view_id=view_id, view_type=view_type, toolbar=toolbar, submenu=submenu)
        doc = etree.XML(res['arch'])
        if view_type == 'tree':
            if self._context.get('default_type', False) not in ('in_invoice', 'in_refund'):
                for node in doc.xpath("//field[@name='approval_user_id']"):
                    doc.remove(node)
            res['arch'] = etree.tostring(doc)
        return res
