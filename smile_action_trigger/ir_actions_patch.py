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

from osv import osv
from safe_eval import new_safe_eval as eval


class IrActionsServer(osv.osv):
    _inherit = 'ir.actions.server'

    def run(self, cr, uid, ids, context=None):
        "Run fix for 'other' type actions"
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
