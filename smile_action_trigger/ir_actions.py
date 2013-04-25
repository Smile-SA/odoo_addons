# -*- encoding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2010 Smile (<http://www.smile.fr>). All Rights Reserved
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

from osv import fields, orm

ACTIONS_EXECUTION_TYPES = [
    ('parallel', 'Parallel'),
    ('sequential', 'Sequential'),
    ('locked', 'Locked'),
]


class IrActionsServer(orm.Model):
    _inherit = 'ir.actions.server'

    _columns = {
        'active': fields.boolean("Active"),
        'run_once': fields.boolean("Run once for all instances", help="Works only from action triggers. "
                                   "If checked, the variable object is a browse record list"),
        'group_by': fields.char('Group by', size=128, help="If run_once is set to True: "
                                "instances are passed to the actions grouped with other instances having the same group_by evaluation"),
        'user_id': fields.many2one('res.users', "User", help="If empty, the action is executed by the current user"),
        'force_rollback': fields.boolean('Force transaction rollback'),
        'specific_thread': fields.boolean('Specific Thread'),
        'execution_type': fields.selection(ACTIONS_EXECUTION_TYPES, 'Execution', required=True),
        'execution_ids': fields.one2many('ir.actions.server.execution', 'action_id', 'Current Executions',
                                         domain=[('state', '=', 'draft')], readonly=True),
    }

    _defaults = {
        'active': True,
        'execution_type': 'parallel',
    }

    def onchange_options(self, cr, uid, ids, field_to_update, force_rollback, specific_thread):
        if (field_to_update == 'force_rollback' and specific_thread) \
                or (field_to_update == 'specific_thread' and force_rollback):
            return {'value': {field_to_update: False}}
        return {}

    def onchange_force_rollback(self, cr, uid, ids, specific_thread, force_rollback):
        return self.onchange_options(cr, uid, ids, 'specific_thread', force_rollback, specific_thread)

    def onchange_specific_thread(self, cr, uid, ids, force_rollback, specific_thread):
        return self.onchange_options(cr, uid, ids, 'force_rollback', force_rollback, specific_thread)

    def _get_execution_args(self, cr, uid, action, context=None):
        context_copy = (context or {}).copy()
        context_copy['launch_actions_execution'] = True
        return {'uid': uid, 'ids': [action.id], 'context': context_copy}

    def _create_execution(self, cr, uid, action, context=None):
        self.pool.get('ir.actions.server.execution').create(cr, uid, {
            'action_id': action.id,
            'locked': action.execution_type == 'locked',
            'launch': context.get('launch_by_trigger') and 'trigger' or 'manual',
            'args': self._get_execution_args(cr, uid, action, context),
        }, context)

    def run(self, cr, uid, ids, context=None):
        context = context or {}
        res = None
        for action in self.browse(cr, uid, ids, context):
            if action.execution_type == 'parallel' or context.get('launch_actions_execution'):
                res = super(IrActionsServer, self).run(cr, uid, [action.id], context)
                if action.execution_ids:
                    action.execution_ids[0].write({'state': 'done'})
            else:
                self._create_execution(cr, uid, action, context)
                # INFO: A constraint prevents the creation of a new execution if a locked action is under execution
            if action.execution_type == 'locked' and not context.get('launch_actions_execution'):
                execution_args = self._get_execution_args(cr, uid, action, context)
                res = self.run(cr, **execution_args)
            if not isinstance(res, bool) and res:
                return res
        return False


class IrActionsServerExecution(orm.Model):
    _name = 'ir.actions.server.execution'
    _description = "Server Action Execution"
    _table = 'ir_act_server_execution'
    _rec_name = 'action_id'

    _columns = {
        'action_id': fields.many2one('ir.actions.server', "Server Action", readonly=True, required=True, ondelete="restrict"),
        'locked': fields.boolean('Locked', readonly=True),
        'create_date': fields.datetime('Create Date', readonly=True),
        'state': fields.selection([('draft', 'To Do'), ('done', 'Done')], "State", readonly=True),
        'launch': fields.selection([('manual', 'manually'), ('trigger', 'by trigger')], "Launched", readonly=True),
        'args': fields.serialized("Arguments", help="", readonly=True),
    }

    _defaults = {
        'state': 'draft',
        'launch': 'manual',
    }

    def _check_locked_action(self, cr, uid, ids, context=None):
        if isinstance(ids, (int, long)):
            ids = [ids]
        executions = self.browse(cr, uid, ids, context=None)
        action_ids = [execution.action_id.id for execution in executions]
        locked_execution_ids = self.search(cr, uid, [
            ('id', 'not in', ids),
            ('state', '=', 'draft'),
            ('action_id', 'in', action_ids),
            ('locked', '=', True),
        ], context=context)
        if locked_execution_ids:
            return False
        return True

    _constraints = [
        (_check_locked_action, 'This action is under execution!', ['action_id'])
    ]

    def auto_execute(self, cr, uid, context=None):
        action_obj = self.pool.get('ir.actions.server')
        ids = self.search(cr, uid, [('state', '=', 'draft'), ('locked', '=', False)], context=context)
        for execution in self.browse(cr, uid, ids, context):
            action_obj.run(cr, **execution.args)
        return True
