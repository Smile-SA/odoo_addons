# -*- coding: utf-8 -*-

import time

from odoo import api, fields, models
from odoo.tools.safe_eval import safe_eval


class ChecklistTask(models.Model):
    _name = 'checklist.task'
    _description = 'Checklist Task'
    _order = 'sequence'

    name = fields.Char(size=128, required=True, translate=True)
    checklist_id = fields.Many2one('checklist', 'Checklist', required=True, ondelete='cascade')
    model_id = fields.Many2one('ir.model', 'Model', related='checklist_id.model_id')
    condition = fields.Char('Condition', size=256, required=True, help="object in localcontext", default='True')
    active = fields.Boolean('Active', default=True)
    action_id = fields.Many2one('ir.actions.server', 'Action')
    sequence = fields.Integer('Priority', required=True, default=15)
    active_field = fields.Boolean("Field 'Active'", related='checklist_id.active_field')
    mandatory = fields.Boolean('Required to make active object')
    field_ids = fields.One2many('checklist.task.field', 'task_id', 'Fields', required=True)

    @api.one
    def _manage_task_instances(self, records=None):
        if records:
            records = records.sudo()
        else:
            records = self.env[self.model_id.model].sudo().with_context(active_test=False).search([])
        for record in records.with_context(active_test=False):
            condition_checked = safe_eval(self.condition, {'object': record, 'time': time})
            task_inst = record.checklist_task_instance_ids.filtered(lambda i: i.task_id == self)
            if condition_checked and not task_inst:
                task_inst.create({'task_id': self.id, 'res_id': record.id})
            elif not condition_checked and task_inst:
                task_inst.unlink()
            checklists = record.checklist_task_instance_ids.mapped('checklist_id')
            checklists.compute_progress_rates(record.with_context(checklist_computation=True))

    @api.model
    def create(self, vals):
        task = super(ChecklistTask, self).create(vals)
        task._manage_task_instances()
        return task

    @api.multi
    def write(self, vals):
        for task in self:
            taskinfo = task.read(vals.keys(), load='_classic_write')[0]
            try:
                shared_items = set(taskinfo.items()) & set(vals.items())
            except:  # Case of x2m fields
                shared_items = {}
            if len(shared_items) == len(vals):
                self -= task
        if not self:
            return True
        checklists = set([task.checklist_id for task in self])
        result = super(ChecklistTask, self).write(vals)
        self._manage_task_instances()
        # Recompute only previous ones because new ones are recomputed in _manage_task_instances
        for checklist in checklists:
            checklist.compute_progress_rates()
        return result

    @api.multi
    def unlink(self):
        checklists = set([task.checklist_id for task in self])
        result = super(ChecklistTask, self).unlink()
        for checklist in checklists:
            checklist.compute_progress_rates()
        return result


class ChecklistTaskField(models.Model):
    _name = 'checklist.task.field'
    _description = 'Checklist Task Field'

    name = fields.Char(size=128, required=True, translate=True)
    task_id = fields.Many2one('checklist.task', 'Task', required=True, ondelete="cascade")
    expression = fields.Text('Expression', required=True,
                             help="You can use the following variables: object, time")
