# -*- coding: utf-8 -*-
##############################################################################
#
#    odoo, Open Source Management Solution
#    Copyright (C) 2017 Smile (<http://www.smile.fr>). All Rights Reserved
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
