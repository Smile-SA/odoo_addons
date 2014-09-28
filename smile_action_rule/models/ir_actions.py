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

from openerp import api, fields, models, _
from openerp.exceptions import Warning


class ServerAction(models.Model):
    _inherit = 'ir.actions.server'

    execution_mode = fields.Selection([
        ('synchronous', 'Synchronous'),
        ('asynchronous', 'Asynchronous'),
        ('locked', 'Locked'),
    ], 'Execution Mode', required=True, default='synchronous')

    @api.multi
    def _get_execution_args(self):
        assert len(self) == 1, 'This option should only be used for a single id at a time.'
        context = (self._context or {}).copy()
        context['force_execution'] = True
        return {'uid': self._uid, 'ids': self._ids, 'context': context}

    @api.multi
    def _create_execution(self):
        assert len(self) == 1, 'This option should only be used for a single id at a time.'
        self.env['ir.actions.server.execution'].create({
            'action_id': self.id,
            'locked': self.execution_mode == 'locked',
            'args': self._get_execution_args(),
        })

    def run(self, cr, uid, ids, context=None):
        res = None
        context = context or {}
        for action in self.browse(cr, uid, ids, context):
            if action.execution_mode == 'synchronous' or context.get('force_execution'):
                res = super(ServerAction, self).run(cr, uid, [action.id], context)
                if action.execution_ids:
                    action.execution_ids[0].write({'state': 'done'})
            else:
                action._create_execution()
                # INFO: A constraint prevents the creation of a new execution if a locked action is under execution
            if action.execution_mode == 'locked' and not context.get('force_execution'):
                execution_args = action._get_execution_args()
                res = self.run(cr, **execution_args)
            if not isinstance(res, bool) and res:
                return res
        return False


class ServerActionExecution(models.Model):
    _name = 'ir.actions.server.execution'
    _description = "Server Action Execution"
    _table = 'ir_act_server_execution'
    _rec_name = 'action_id'

    action_id = fields.Many2one('ir.actions.server', "Server Action", readonly=True, required=True, ondelete="restrict")
    create_date = fields.Datetime('Create Date', readonly=True)
    locked = fields.Boolean('Locked', readonly=True)
    state = fields.Selection([('draft', 'To Do'), ('done', 'Done')], "State", readonly=True, default='draft')
    args = fields.Text("Arguments", help="Execution context", readonly=True)

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
            raise Warning(_('This action is under execution!'))
        return True

    @api.model
    def execute(self):
        executions = self.search([('state', '=', 'draft'), ('locked', '=', False)])
        for execution in executions:
            self.pool['ir.actions.server'].run(self._cr, **execution.args)
        return True
