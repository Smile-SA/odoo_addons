# -*- coding: utf-8 -*-
# (C) 2011 Smile (<http://www.smile.fr>)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import api, models, _


class Base(models.AbstractModel):
    _inherit = 'base'

    @api.one
    def _get_checklist_task_instances(self):
        domain = [
            ('task_id.checklist_id.model_id.model', '=', self._name),
            ('res_id', '=', self.id),
        ]
        self.x_checklist_task_instance_ids = \
            self.env['checklist.task.instance'].search(domain)

    @api.multi
    def _manage_checklist_task_instances(self):
        if self and not self._context.get('checklist_computation') and \
                'x_checklist_task_instance_ids' in self._fields:
            Checklist = self.env['checklist']
            if hasattr(Checklist, '_get_checklist_by_model'):
                checklist_id = Checklist._get_checklist_by_model().get(
                    self._name)
                Checklist.browse(checklist_id).task_ids. \
                    _manage_task_instances(self)

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
