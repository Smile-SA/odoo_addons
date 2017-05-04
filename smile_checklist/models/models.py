# -*- coding: utf-8 -*-

from openerp import api, models


@api.multi
def _manage_checklist_task_instances(self):
    if self and not self._context.get('checklist_computation') and 'checklist_task_instance_ids' in self._fields:
        checklist_obj = self.env['checklist']
        if hasattr(checklist_obj, '_get_checklist_by_model'):
            checklist_id = checklist_obj._get_checklist_by_model(self._cr, self._uid).get(self._name)
            checklist_obj.browse(checklist_id).task_ids._manage_task_instances(self)

models.Model._manage_checklist_task_instances = _manage_checklist_task_instances
