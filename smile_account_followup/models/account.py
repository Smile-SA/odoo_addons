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

from operator import attrgetter
from openerp import models, fields, api


class AccountInvoice(models.Model):
    _inherit = 'account.invoice'

    level_reminder_id = fields.Many2one('level.reminder', store=True, string='Recovery Level', compute='_compute_level_reminder')
    action_reminder_ids = fields.One2many('action.reminder', 'account_invoice_id', string='Followup actions', copy=False,
                                          readonly=True, states={'open': [('readonly', False)]})

    @api.multi
    @api.depends('action_reminder_ids')
    def _compute_level_reminder(self):
        for inv in self:
            level_reminder_id = False
            if inv.action_reminder_ids:
                actiond_ids = sorted(inv.action_reminder_ids, key=attrgetter('create_date'))
                level_reminder_id = actiond_ids[-1].level_reminder_id.id
            inv.level_reminder_id = level_reminder_id
