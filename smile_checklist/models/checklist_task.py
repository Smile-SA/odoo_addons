# -*- coding: utf-8 -*-

from odoo import api, fields, models


class ChecklistTask(models.Model):
    _name = 'checklist.task'
    _description = 'Checklist Task'
    _order = 'sequence'

    name = fields.Char(required=True, translate=True)
    active = fields.Boolean(default=True)
    sequence = fields.Integer('Priority', required=True, default=15)
    checklist_id = fields.Many2one(
        'checklist', 'Checklist', required=True, ondelete='cascade',
        auto_join=True)
    active_field = fields.Boolean(
        "Field 'Active'", related='checklist_id.active_field')
    mandatory = fields.Boolean('Required to make active object')
    filter_domain = fields.Char('Apply on')
    complete_domain = fields.Char('Complete if')
    model = fields.Char(related='checklist_id.model_id.model')

    @api.model
    def create(self, vals):
        task = super(ChecklistTask, self).create(vals)
        task._manage_task_instances()
        return task

    @api.multi
    def write(self, vals):
        self = self._filter_tasks_to_update(vals)
        if not self:
            return True
        checklists = self.mapped('checklist_id')
        result = super(ChecklistTask, self).write(vals)
        self._manage_task_instances()
        # Recompute only old checklists linked to tasks before updating
        (checklists - self.mapped('checklist_id'))._compute_progress_rates()
        return result

    @api.multi
    def unlink(self):
        checklists = self.mapped('checklist_id')
        result = super(ChecklistTask, self).unlink()
        checklists._compute_progress_rates()
        return result

    @api.multi
    def _filter_tasks_to_update(self, vals):
        for task in self:
            taskinfo = task.read(vals.keys(), load='_classic_write')[0]
            try:
                shared_items = set(taskinfo.items()) & set(vals.items())
            except Exception:  # Case of x2m fields
                shared_items = {}
            if len(shared_items) == len(vals):
                self -= task
        return self

    @api.multi
    def _manage_task_instances(self, records=None):
        if not records:
            records = self.env[self.checklist_id.model_id.model].sudo(). \
                with_context(active_test=False).search([])
        self._update_task_instances_list(records)
        self.mapped('checklist_id')._compute_progress_rates(
            records.with_context(checklist_computation=True))

    @api.one
    def _update_task_instances_list(self, records):
        for record in records.sudo().with_context(active_test=False):
            task_inst = record.x_checklist_task_instance_ids.filtered(
                lambda inst: inst.task_id == self)
            valid_record = record.filtered_from_domain(self.filter_domain)
            if valid_record and not task_inst:
                task_inst.create({'task_id': self.id, 'res_id': record.id})
            elif not valid_record and task_inst:
                task_inst.unlink()
