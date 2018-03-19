# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2014 Smile (<http://www.smile.fr>).
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

from odoo import api, fields, models, _
from odoo.exceptions import UserError


class ServerAction(models.Model):
    _inherit = 'ir.actions.server'
    _description = 'Server Actions'

    execution_mode = fields.Selection([
        ('synchronous', 'Synchronous'),
        ('asynchronous', 'Asynchronous'),
        ('locked', 'Locked'),
    ], 'Execution Mode', required=True, default='synchronous')
    execution_ids = fields.One2many('ir.actions.server.execution', 'action_id',
                                    'Executions', readonly=True)

    @api.multi
    def _create_execution(self):
        self.ensure_one()
        self.env['ir.actions.server.execution'].create({
            'action_id': self.id,
            'locked': self.execution_mode == 'locked',
            'context': repr(self._context),
        })

    @api.multi
    def run(self):
        res = False
        for action in self:
            if action.execution_mode == 'synchronous' or \
                    self._context.get('force_execution'):
                res = super(ServerAction, action).run()
                if action.execution_ids:
                    action.execution_ids[0].write({'state': 'done'})
            else:
                action._create_execution()
                # INFO: A constraint prevents the creation of a new execution
                # if a locked action is under execution
            if action.execution_mode == 'locked' and \
                    not self._context.get('force_execution'):
                res = action.with_context(force_execution=True).run()
            if not isinstance(res, bool) and res:
                return res
        return False


class ServerActionExecution(models.Model):
    _name = 'ir.actions.server.execution'
    _description = "Server Action Execution"
    _table = 'ir_act_server_execution'
    _rec_name = 'action_id'

    action_id = fields.Many2one(
        'ir.actions.server', "Server Action",
        readonly=True, required=True, ondelete="restrict")
    create_date = fields.Datetime('Create Date', readonly=True)
    locked = fields.Boolean('Locked', readonly=True)
    state = fields.Selection(
        [('draft', 'To Do'), ('done', 'Done')],
        "State", readonly=True, default='draft')
    context = fields.Text("Context", readonly=True)

    @api.one
    @api.constrains('action_id')
    def _check_locked_action(self):
        domain = [
            ('id', '!=', self.id),
            ('state', '=', 'draft'),
            ('action_id', '=', self.action_id.id),
            ('locked', '=', True),
        ]
        if self.search_count(domain):
            raise UserError(_('This action is under execution!'))
        return True

    @api.model
    def execute(self):
        executions = self.search([
            ('state', '=', 'draft'),
            ('locked', '=', False),
        ])
        for execution in executions:
            context = eval(execution.context)
            execution.action_id.with_context(context).run()
        return True
