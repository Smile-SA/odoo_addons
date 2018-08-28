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

from datetime import datetime, timedelta

from openerp import models, api, fields, exceptions
from openerp.tools.translate import _


class WizardAccountFollowup(models.TransientModel):
    _name = "wizard.account.followup"

    start_invoice_date = fields.Date(string="Start")
    stop_invoice_date = fields.Date(string="End", required=True, default=fields.datetime.now())
    start_due_date = fields.Date(string="Start")
    stop_due_date = fields.Date(string="End", required=True, default=fields.datetime.now())
    partner_ids = fields.Many2many('res.partner', string="Customers", domain=[('customer', '=', True)])
    name = fields.Char(required=True, string='Description')
    level_reminder_id = fields.Many2one('level.reminder', required=True, string='Level reminder')
    responsible_id = fields.Many2one('res.users', required=True, string='Responsible', domain=[('user_profile', '=', False)])
    date = fields.Date(string='Due date', required=True, default=fields.datetime.now())
    page_peer_partner = fields.Boolean(string="Page peer partner", help="Show partner data: Page peer partner", default=True)

    @api.onchange('level_reminder_id')
    def _onchange_level_reminder(self):
        due_date = datetime.now().date()
        if self.level_reminder_id:
            due_date = due_date + timedelta(days=self.level_reminder_id.due_term)
        self.date = due_date

    @api.multi
    def create_action(self):
        self.ensure_one()
        active_ids = self._context.get('active_ids', [])
        vals = {'name': self.name,
                'level_reminder_id': self.level_reminder_id.id,
                'responsible_id': self.responsible_id.id,
                'date': self.date}
        for inv in self.env['account.invoice'].browse(active_ids):
            if inv.state in ('draft', 'paid'):
                raise exceptions.Warning(_('Invalid action!'), _('You can not create actions for invoices in draft or paid state!'))
            vals.update({'account_invoice_id': inv.id})
            self.env['action.reminder'].create(vals)
        return {'type': 'ir.actions.act_window_close'}

    @api.model
    def get_partner_invoices(self, partner_ids, invoices):
        """
        @partner_ids: list partner_id
        @invoices: records invoices (list)
        return = [partner_name, ref, phone, mobile, [invoice_ids]]
        """
        data = {}
        for invoice in invoices:
            if invoice.partner_id.id in partner_ids:
                if str(invoice.partner_id.id) in data:
                    if invoice.id not in data[str(invoice.partner_id.id)][4]:
                        data[str(invoice.partner_id.id)][4].append(invoice.id)
                else:
                    data.update({str(invoice.partner_id.id): [invoice.partner_id.name,
                                                              invoice.partner_id.ref or '',
                                                              invoice.partner_id.phone or '',
                                                              invoice.partner_id.mobile or '',
                                                              [invoice.id]]})
        return data.values()

    @api.multi
    def button_print(self):
        self.ensure_one()
        datas = {'form': self.read()[0]}
        # Filter
        invoice_ids = self._context.get('active_ids', [])
        filter_domain = [('id', 'in', invoice_ids),
                         ('date_invoice', '<=', datas['form']['stop_invoice_date']),
                         ('date_due', '<=', datas['form']['stop_due_date'])]
        if datas['form']['start_due_date']:
            filter_domain.append(('date_due', '>=', datas['form']['start_due_date']))
        if datas['form']['start_invoice_date']:
            filter_domain.append(('date_invoice', '>=', datas['form']['start_invoice_date']))
        # Invoices
        invoices = self.env['account.invoice'].search(filter_domain)
        # Partner
        partner_ids = datas['form']['partner_ids'] or list(set([invoice.partner_id.id for invoice in invoices]))
        # Datas
        datas['form'].update({'result': self.get_partner_invoices(partner_ids, invoices)})
        return self.env['report'].get_action(records=self.env['report'],
                                             report_name='smile_account_followup.report_unpaid_invoice',
                                             data=datas)
