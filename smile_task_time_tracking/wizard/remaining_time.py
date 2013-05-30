# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2013 Smile (<http://www.smile.fr>).
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

from openerp.osv import fields
from openerp.osv.osv import except_osv
from openerp.osv.orm import TransientModel
import openerp.addons.decimal_precision as dp


class RemainingTimeWizard(TransientModel):
    _name = 'project.task.remaining_time.wizard'
    _description = "Task's Remaining Time Wizard"

    def _get_task_id(self, context=None):
        if context is None:
            context = {}
        task_ids = context.get('active_ids', [])
        if len(task_ids) != 1 or context.get('active_model', None) != 'project.task':
            raise except_osv('Error', 'Wrong context.')
        return task_ids[0]

    def view_init(self, cr, uid, fields_list, context=None):
        return self._get_task_id(context)

    _columns = {
        'is_time_ratio': fields.boolean("Display remaining time as a ratio", help="Let the user enter the new remaining time as a ratio to its current value."),
        'new_remaining_time_ratio': fields.integer('New Remaining Time Ratio (%)', help="New value of task's total remaining time, as a ratio of its current value."),
        # Fields below are alter-egos of the ones defined in project.project.py:task() class
        'planned_time': fields.float('Initially Planned Time', readonly=True, help='Estimated time to do the task, usually set by the project manager when the task is in draft state.'),
        'effective_time': fields.float('Time Spent', readonly=True, help="Computed using the sum of the task work done."),
        'current_remaining_time_value': fields.float('Current Remaining Time', digits=(16,2), readonly=True, help="Current value of task's total remaining time."),
        'new_remaining_time_value': fields.float('New Remaining Time Value', digits=(16,2), required=True, help="New value of task's total remaining time."),
    }

    _defaults = {
        'is_time_ratio': False,
    }

    def onchange_remaining_time(self, cr, uid, ids, current_value, new_value, new_ratio, value_update, context=None):
        if context is None:
            context = {}
        res = {}
        if value_update:
            res['new_remaining_time_value'] = current_value * (new_ratio / 100.0)
        else:
            if not current_value:
                res['new_remaining_time_ratio'] = 0
            else:
                res['new_remaining_time_ratio'] = int((new_value * 100.0) / current_value)
        return {'value': res}

    def button_update_remaining_time(self, cr, uid, ids, context=None):
        ids = isinstance(ids, (tuple, list)) and ids or [ids]
        if not ids or len(ids) > 1:
            return False
        wizard = self.browse(cr, uid, ids[0], context)
        task_id = self._get_task_id(context)
        # Force proper computation of new remaining time value: the onchange_remaining_time() is not enough to get reliable values. The onchange is not triggered if the field currently edited doesn't loose focus.
        remaining_time = wizard.new_remaining_time_value
        if wizard.is_time_ratio:
            remaining_time = self.onchange_remaining_time(cr, uid, None, wizard.current_remaining_time_value, remaining_time, wizard.new_remaining_time_ratio, wizard.is_time_ratio)['value']['new_remaining_time_value']
        # Update task's remaining time. This will automaticcaly trigger the creation of a project.task.tracking_line
        self.pool.get('project.task').write(cr, uid, task_id, {'remaining_hours': remaining_time}, context=context)
        # Go back to the task we've just updated
        return {
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'view_id': self.pool.get('ir.model.data').get_object_reference(cr, uid, 'project', 'view_task_form2')[1],
            'res_model': 'project.task',
            'res_id': task_id,
            'target': 'current',
            'context': context,
        }

    def button_close(self, cr, uid, ids, context=None):
        return {'type': 'ir.actions.act_window_close'}
