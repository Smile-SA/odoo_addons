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

from openerp import api, fields, models, SUPERUSER_ID, tools, _
from openerp.exceptions import Warning
from openerp.modules.registry import Registry

from checklist_decorators import checklist_view_decorator, checklist_create_decorator, checklist_write_decorator


def update_checklists(load):
    def wrapper(self, cr, module):
        res = load(self, cr, module)
        if self.get('checklist'):
            self.get('checklist')._update_models(cr, SUPERUSER_ID)
        return res
    return wrapper


class Checklist(models.Model):
    _name = 'checklist'
    _description = 'Checklist'

    name = fields.Char(size=128, required=True, translate=True)
    model_id = fields.Many2one('ir.model', 'Model', required=True)
    model = fields.Char(related='model_id.model', readonly=True)
    active = fields.Boolean('Active', default=True)
    active_field = fields.Boolean("Has an 'Active' field", compute='_get_active_field', default=False)
    action_id = fields.Many2one('ir.actions.server', 'Actions')
    view_ids = fields.Many2many('ir.ui.view', 'checklist_view_rel', 'view_id', 'checklist_id', 'Views')
    task_ids = fields.One2many('checklist.task', 'checklist_id', 'Tasks')

    @api.one
    def _get_active_field(self):
        if self.model_id:
            model = self.env[self.model_id.model]
            self.active_field = 'active' in model._fields.keys() + model._columns.keys()

    @api.one
    @api.constrains('model_id')
    def _check_unique_checklist_per_object(self):
        count = self.search_count([('model_id', '=', self.model_id.id)])
        if count > 1:
            raise Warning(_('A checklist has already existed for this model !'))

    @tools.cache(skiparg=3)
    def _get_checklist_by_model(self, cr, uid):
        res = {}
        for checklist in self.browse(cr, SUPERUSER_ID, self.search(cr, SUPERUSER_ID, [])):
            res[checklist.model] = checklist.id
        return res

    @staticmethod
    def _get_checklist_task_inst(self):
        domain = [('task_id.checklist_id.model_id.model', '=', self._name), ('res_id', '=', self.id)]
        self.checklist_task_instance_ids = self.env['checklist.task.instance'].with_context(active_test=True).search(domain)

    @api.model
    def _update_models(self, models=None):
        if not models:
            models = dict([(checklist.model_id, checklist) for checklist in self.search([])])
        for model, checklist in models.iteritems():
            model_obj = self.env[model.model]
            if checklist:
                cls = model_obj.__class__
                setattr(cls, '_get_checklist_task_inst', api.one(api.depends()(Checklist._get_checklist_task_inst)))
                model_obj._add_field('checklist_task_instance_ids', fields.One2many('checklist.task.instance',
                                                                                    string='Checklist Task Instances',
                                                                                    compute='_get_checklist_task_inst'))
                model_obj._setup_fields()
                model_obj._add_field('total_progress_rate', fields.Float('Progress Rate', digits=(16, 2)))
                model_obj._add_field('total_progress_rate_mandatory', fields.Float('Mandatory Progress Rate', digits=(16, 2)))
                self.pool[model.model]._field_create(self._cr, self._context)
            else:
                for field in ('checklist_task_instance_ids', 'total_progress_rate', 'total_progress_rate_mandatory'):
                    if field in model_obj._columns:
                        del model_obj._columns[field]
                    if field in model_obj._fields:
                        del model_obj._fields[field]
            if model_obj.create.__name__ != 'checklist_wrapper':
                model_obj._patch_method('create', checklist_create_decorator())
            if model_obj.write.__name__ != 'checklist_wrapper':
                model_obj._patch_method('write', checklist_write_decorator())
            if model_obj.fields_view_get.__name__ != 'checklist_wrapper':
                model_obj._patch_method('fields_view_get', checklist_view_decorator())
        self.clear_caches()

    def __init__(self, pool, cr):
        super(Checklist, self).__init__(pool, cr)
        setattr(Registry, 'load', update_checklists(getattr(Registry, 'load')))
 
    @api.model
    def create(self, vals):
        checklist = super(Checklist, self).create(vals)
        self._update_models({self.env['ir.model'].browse(vals['model_id']): checklist})
        return checklist

    @api.multi
    def write(self, vals):
        if 'model_id' in vals:
            models = dict([(checklist.model_id, False) for checklist in self])
            if vals['model_id']:
                models.update({self.env['ir.model'].browse(vals['model_id']): checklist})
        result = super(Checklist, self).write(vals)
        if 'model_id' in vals:
            self._update_models(models)
        return result
 
    @api.multi
    def unlink(self):
        models = dict([(checklist.model_id, False) for checklist in self])
        result = super(Checklist, self).unlink()
        self._update_models(models)
        return result

    @api.one
    def compute_progress_rates(self, rec_ids=None):
        model_obj = self.env[self.model]
        if rec_ids:
            recs = model_obj.browse(rec_ids)
        else:
            recs = model_obj.with_context(active_test=False).search([])
        for rec in recs:
            ctx = {'active_id': rec.id, 'active_ids': [rec.id]}
            for task_inst in rec.checklist_task_instance_ids:
                old_progress_rate = task_inst.progress_rate
                if task_inst.task_id.field_ids:
                    task_inst.progress_rate = 100.0 * len(task_inst.field_ids_filled) / len(task_inst.task_id.field_ids)
                else:
                    task_inst.progress_rate = 100.0
                if task_inst.task_id.action_id and old_progress_rate != task_inst.progress_rate == 100.0:
                    task_inst.task_id.action_id.with_context(**ctx).run()
            total_progress_rate = 0.0
            if rec.checklist_task_instance_ids:
                total_progress_rate = sum(i.progress_rate for i in rec.checklist_task_instance_ids) \
                    / len(rec.checklist_task_instance_ids)
            vals = {'total_progress_rate': total_progress_rate}
            if self.active_field:
                total_progress_rate_mandatory = 0.0
                mandatory_inst = [i for i in rec.checklist_task_instance_ids if i.mandatory]
                if mandatory_inst:
                    total_progress_rate_mandatory = sum(i.progress_rate for i in rec.checklist_task_instance_ids if i.mandatory) \
                        / len(mandatory_inst)
                vals['total_progress_rate_mandatory'] = total_progress_rate_mandatory
                if vals['total_progress_rate_mandatory'] == 100.0:
                    vals['active'] = True
            old_total_progress_rate = rec.total_progress_rate
            rec.write(vals)
            if self.action_id and old_total_progress_rate != rec.total_progress_rate == 100.0:
                self.action_id.with_context(**ctx).run()


class ChecklistTask(models.Model):
    _name = 'checklist.task'
    _description = 'Checklist Task'

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

    @api.model
    def create(self, vals):
        task = super(ChecklistTask, self).create(vals)
        model = self.env[task.model_id.model].with_context(active_test=False)
        for record in model.search([]):
            self.env['checklist.task.instance'].create({'task_id': task.id, 'res_id': record.id})
        task.checklist_id.compute_progress_rates()
        return task

    @api.multi
    def write(self, vals):
        checklists = set([task.checklist_id for task in self])
        result = super(ChecklistTask, self).write(vals)
        for checklist in checklists | set([task.checklist_id for task in self]):
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


class ChecklistTaskInstance(models.Model):
    _name = 'checklist.task.instance'
    _description = 'Checklist Task Instance'

    task_id = fields.Many2one('checklist.task', 'Checklist Task', required=True, ondelete='cascade')
    sequence = fields.Integer('Priority', related='task_id.sequence', store=True)
    checklist_id = fields.Many2one('checklist', 'Checklist', related='task_id.checklist_id')
    model_id = fields.Many2one('ir.model', 'Model', related='checklist_id.model_id')
    name = fields.Char(size=128, related='task_id.name')
    mandatory = fields.Boolean('Required', help='Required to make active object', related='task_id.mandatory')
    res_id = fields.Integer('Resource ID', index=True, required=True)
    active = fields.Boolean(compute='_get_activity')
    field_ids_to_fill = fields.One2many('checklist.task.field', string='Fields to fill', compute='_get_activity')
    field_ids_filled = fields.One2many('checklist.task.field', string='Filled fields', compute='_get_activity')
    progress_rate = fields.Float('Progress Rate', digits=(16, 2), default=0.0)

    @api.one
    @api.depends()
    def _get_activity(self):
        localdict = {'object': self.env[self.model_id.model].browse(self.res_id),
                     'time': time}
        self.active = self.task_id.active and eval(self.task_id.condition, localdict)
        field_ids_to_fill = []
        field_ids_filled = []
        for field in self.task_id.field_ids:
            try:
                exec "result = bool(%s)" % str(field.expression) in localdict
                if 'result' not in localdict or not localdict['result']:
                    field_ids_to_fill.append(field.id)
                else:
                    field_ids_filled.append(field.id)
            except:
                pass
#         self.field_ids_to_fill = field_ids_to_fill
#         self.field_ids_filled = field_ids_filled
        self._cache['field_ids_to_fill'] = field_ids_to_fill
        self._cache['field_ids_filled'] = field_ids_filled
