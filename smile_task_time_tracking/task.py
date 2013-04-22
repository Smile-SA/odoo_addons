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
from openerp.osv.osv import osv, except_osv
from openerp.tools.translate import _
import openerp.addons.decimal_precision as dp


class Task(osv):
    _inherit = 'project.task'

    def _get_remaining_time_line(self, cr, uid, ids, field_name, arg, context=None):
        if context is None:
            context = {}
        result = {}
        for task in self.browse(cr, uid, ids, context=context):
            remaining_time_line = [l for l in task.remaining_time_line_ids if not l.archived]
            result[task.id] = remaining_time_line and remaining_time_line[0] or False
        return result

    _columns = {
      'remaining_time_line_ids': fields.one2many('project.task.remaining_time.line', 'task_id', string='Remaining Time Lines', readonly=True, help="Remaining time history."),
    }

    def _check_active_remaining_time_lines(self, cr, uid, ids, context=None):
        if context is None:
            context = {}
        for task in self.browse(cr, uid, ids, context):
            active_lines = [l for l in task.remaining_time_line_ids if not l.archived]
            if len(active_lines) > 1:
                return False
        return True

    _constraints = [
        (_check_active_remaining_time_lines, "No more than one active remaining time line is allowed.", ['remaining_time_line_ids']),
    ]


class RemainingTimeLine(osv):
    _name = 'project.task.remaining_time.line'
    _order = "archived asc, write_date desc"

    _columns = {
      'task_id': fields.many2one('project.task', 'Task', readonly=True, required=True, ondelete='cascade', help="Task this remaining time line is attached to."),


      'write_date': fields.datetime("Modification Date", readonly=True, required=True, help="Last date when the budget line was updated."),
      'create_uid':  fields.many2one('res.users', 'Author', readonly=True, required=True, help="The user who created this budget line."),
      'archived': fields.boolean('Archived', readonly=True, help="Flag a budget line as archived."),
    }

    _defaults = {
        'archived': False,
    }

    _sql_constraints = [
    ]


RemainingTimeLine()
Task()
