# -*- coding: utf-8 -*-

from odoo import api, models, _


@api.multi
def _manage_checklist_task_instances(self):
    if self and not self._context.get('checklist_computation') and 'checklist_task_instance_ids' in self._fields:
        checklist_obj = self.env['checklist']
        if hasattr(checklist_obj, '_get_checklist_by_model'):
            checklist_id = checklist_obj._get_checklist_by_model().get(self._name)
            checklist_obj.browse(checklist_id).task_ids._manage_task_instances(self)

@api.multi
def open_checklist(self):
    self.ensure_one()
    return {
        'name': _('Checklist'),
        'type': 'ir.actions.client',
        'tag': 'checklist_instance_view',
        'target': 'new',
        'context': {'res_model': self._name, 'res_id': self.id},
    }

models.Model._manage_checklist_task_instances = _manage_checklist_task_instances
models.Model.open_checklist = open_checklist
