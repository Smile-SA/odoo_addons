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

import time

from osv import fields, osv
from safe_eval import new_safe_eval as eval


class IrActionsServer(osv.osv):
    _inherit = 'ir.actions.server'

    _columns = {
        'active': fields.boolean("Active"),
        'run_once': fields.boolean("Run once for all instances", help="Works only from action triggers. If checked, the variable object is a browse record list"),
        'group_by': fields.char('Group by', size=128, help="If run_once is set to True: instances are passed to the actions grouped with other instances having the same group_by evaluation"),
        'user_id': fields.many2one('res.users', "User", help="If empty, the action is executed by the current user"),
        'force_rollback': fields.boolean('Force transaction rollback'),
        'specific_thread': fields.boolean('Specific Thread'),
    }

    _defaults = {
        'active': True,
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

    def run(self, cr, uid, ids, context=None):
        """
        run fix for 'other' type actions
        """
        act_ids = []

        for action in self.browse(cr, uid, ids, context):
            obj_pool = self.pool.get(action.model_id.model)
            obj = obj_pool.browse(cr, uid, context['active_id'], context=context)
            cxt = {
                'context': context,
                'object': obj,
                'time': time,
                'cr': cr,
                'pool': self.pool,
                'uid': uid
            }
            expr = eval(str(action.condition), cxt)
            if not expr:
                continue
            if action.state == 'other':
                res = []
                for act in action.child_ids:
                    if not context.get('active_id'):
                        context['active_id'] = context['active_ids'][0]
                    result = self.run(cr, uid, [act.id], context)
                    if result:
                        res.append(result)
                return res
        else:
            act_ids.append(action.id)

        if act_ids:
            return super(IrActionsServer, self).run(cr, uid, act_ids, context)
        else:
            return False

IrActionsServer()
