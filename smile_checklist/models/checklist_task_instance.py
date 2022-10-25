# -*- coding: utf-8 -*-
# (C) 2020 Smile (<http://www.smile.fr>)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import api, fields, models
from odoo.tools.safe_eval import safe_eval


class ChecklistTaskInstance(models.Model):
    _name = 'checklist.task.instance'
    _description = 'Checklist Task Instance'
    _order = 'sequence'

    task_id = fields.Many2one(
        'checklist.task', 'Checklist Task',
        required=True, ondelete='cascade', readonly=True, auto_join=True)
    res_id = fields.Integer(
        'Resource ID', index=True, required=True, readonly=True)
    name = fields.Char(related='task_id.name', readonly=True)
    mandatory = fields.Boolean(
        'Required to make record active',
        related='task_id.mandatory', readonly=True)
    sequence = fields.Integer(
        'Priority', related='task_id.sequence', store=True, readonly=True)
    active = fields.Boolean(compute='_compute_active', store=True)
    complete = fields.Boolean(readonly=True)

    @api.depends('task_id.filter_domain', 'task_id.active')
    def _compute_active(self):
        for task in self:
            if task and task.task_id:
                task.active = task.task_id.active
                record = self.env[task.task_id.model].browse(task.res_id)
                if not record.filtered_domain(safe_eval(task.task_id.filter_domain)):
                    task.active = False
