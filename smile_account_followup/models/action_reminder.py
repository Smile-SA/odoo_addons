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

from openerp import models, fields, api
from openerp.tools.translate import _


class LevelReminderType(models.Model):
    _name = 'level.reminder.type'

    name = fields.Char(required=True, translate=True)


class LevelReminder(models.Model):
    _name = 'level.reminder'

    name = fields.Char(required=True, string='Description', translate=True)
    code = fields.Char(required=True)
    due_term = fields.Integer(string='Default due term (days)')
    type_id = fields.Many2one('level.reminder.type', required=True, string='Type')

    _sql_constraints = [
        ('unique_code', 'UNIQUE (code)', _('Reminder level code must be unique')),
    ]

#     @api.multi
#     def name_get(self):
#         return [(level.id, level.code) for level in self]


class ActionReminder(models.Model):
    _name = 'action.reminder'

    name = fields.Char(required=True, string='Description')
    level_reminder_id = fields.Many2one('level.reminder', required=True, string='Level reminder', copy=False)
    date = fields.Date(string='Due date', required=True, default=fields.datetime.now())
    account_invoice_id = fields.Many2one('account.invoice', required=True, string='Account invoice', copy=False,
                                         domain=[('type', '=', 'out_invoice'), ('state', '=', 'open')])
    partner_id = fields.Many2one(related='account_invoice_id.partner_id', store=True, readonly=True)
    debt_amount = fields.Float(string='Debt amount')
    responsible_id = fields.Many2one('res.users', required=True, string='Responsible', domain=[('user_profile', '=', False)])
    action_done = fields.Boolean(string='Action done')
    action_dropped = fields.Boolean(string='Action dropped')

    @api.onchange('level_reminder_id')
    def _onchange_level_reminder(self):
        due_date = datetime.now().date()
        if self.level_reminder_id:
            due_date = due_date + timedelta(days=self.level_reminder_id.due_term)
        self.date = due_date

    @api.onchange('action_done')
    def _onchange_action_done(self):
        if self.action_done:
            self.action_dropped = False

    @api.onchange('action_dropped')
    def _onchange_action_dropped(self):
        if self.action_dropped:
            self.action_done = False
