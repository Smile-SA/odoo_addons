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

from openerp import api, models


@api.multi
def _manage_checklist_task_instances(self):
    if not self._context.get('no_checklist') and 'checklist_task_instance_ids' in self._fields:
        checklist_obj = self.pool.get('checklist')
        if checklist_obj and hasattr(checklist_obj, '_get_checklist_by_model'):
            checklist_id = checklist_obj._get_checklist_by_model(self._cr, self._uid).get(self._name)
            tasks = self.env['checklist'].browse(checklist_id).task_ids
            inst_obj = self.env['checklist.task.instance']
            for record in self:
                for task in tasks:
                    task_inst = record.checklist_task_instance_ids.filtered(lambda i: i.task_id == task)
                    condition_checked = eval(task.condition, {'object': record, 'time': time})
                    if condition_checked and not task_inst:
                        inst_obj.create({'task_id': task.id, 'res_id': record.id})
                    elif not condition_checked and task_inst:
                        task_inst.unlink()
                if record.checklist_task_instance_ids:
                    record.checklist_task_instance_ids[0].checklist_id.with_context(no_checklist=True).compute_progress_rates([record.id])

models.Model._manage_checklist_task_instances = _manage_checklist_task_instances
