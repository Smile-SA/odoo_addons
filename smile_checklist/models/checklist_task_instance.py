# -*- coding: utf-8 -*-

import time

from odoo import api, fields, models
from odoo.tools.safe_eval import safe_eval


class ChecklistTaskInstance(models.Model):
    _name = 'checklist.task.instance'
    _description = 'Checklist Task Instance'
    _order = 'sequence'

    task_id = fields.Many2one('checklist.task', 'Checklist Task', required=True, ondelete='cascade', readonly=True)
    sequence = fields.Integer('Priority', related='task_id.sequence', store=True, readonly=True)
    checklist_id = fields.Many2one('checklist', 'Checklist', related='task_id.checklist_id', readonly=True)
    model_id = fields.Many2one('ir.model', 'Model', related='task_id.checklist_id.model_id', readonly=True)
    model = fields.Char(related='model_id.model', readonly=True)
    name = fields.Char(size=128, related='task_id.name', readonly=True)
    mandatory = fields.Boolean('Required to make record active', related='task_id.mandatory', readonly=True)
    res_id = fields.Integer('Resource ID', index=True, required=True, readonly=True)
    active = fields.Boolean(compute='_get_activity', search='_search_activity')
    field_ids_to_fill = fields.One2many('checklist.task.field', string='Fields to fill', compute='_get_activity')
    field_ids_filled = fields.One2many('checklist.task.field', string='Filled fields', compute='_get_activity')
    progress_rate = fields.Float('Progress Rate', digits=(16, 2), default=0.0, readonly=True)

    @api.one
    @api.depends()
    def _get_activity(self):
        self.active = self.task_id.active
        field_ids_to_fill = self.env['checklist.task.field'].browse()
        field_ids_filled = self.env['checklist.task.field'].browse()
        localdict = {'object': self.env[self.model_id.model].browse(self.res_id),
                     'time': time}
        if safe_eval(self.task_id.condition, localdict):
            for field in self.task_id.field_ids:
                try:
                    exec "result = bool(%s)" % str(field.expression) in localdict
                    if 'result' not in localdict or not localdict['result']:
                        field_ids_to_fill |= field
                    else:
                        field_ids_filled |= field
                except:
                    pass
        else:
            self.active = False
        self.field_ids_to_fill = field_ids_to_fill
        self.field_ids_filled = field_ids_filled

    @api.model
    def _search_activity(self, operator, value):
        # TODO: manage task condition
        return [('task_id.active', operator, value)]

    @api.multi
    def read(self, fields=None, load='_classic_read'):
        special = False
        if fields:
            for field in ('fields_to_fill', 'fields_filled'):
                if field in fields:
                    fields.remove(field)
                    special = True
                    break
        res = super(ChecklistTaskInstance, self).read(fields, load)
        if special:
            for info in res:
                task_inst = self.browse(info['id'])
                info['fields_to_fill'] = task_inst.field_ids_to_fill.mapped('name')
                info['fields_filled'] = task_inst.field_ids_filled.mapped('name')
        return res
