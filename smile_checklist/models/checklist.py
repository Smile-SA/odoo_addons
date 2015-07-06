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
from openerp.modules.registry import Registry, RegistryManager
from openerp.tools.safe_eval import safe_eval as eval

import checklist_decorators


def update_checklists(method):
    def wrapper(self, cr, *args, **kwargs):
        res = method(self, cr, *args, **kwargs)
        if self.get('checklist'):
            cr.execute("select relname from pg_class where relname='checklist'")
            if cr.rowcount:
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
    act_window_ids = fields.Many2many('ir.actions.act_window', 'checklist_act_window_rel', 'act_window_id', 'checklist_id', 'Menus')
    view_ids = fields.Many2many('ir.ui.view', 'checklist_view_rel', 'view_id', 'checklist_id', 'Views')
    task_ids = fields.One2many('checklist.task', 'checklist_id', 'Tasks')

    @api.one
    def _get_active_field(self):
        if self.model_id:
            model = self.env[self.model_id.model]
            self.active_field = 'active' in model._fields.keys()

    @api.one
    @api.constrains('model_id')
    def _check_unique_checklist_per_object(self):
        count = self.with_context(active_test=True).search_count([('model_id', '=', self.model_id.id)])
        if count > 1:
            raise Warning(_('A checklist already exists for this model !'))

    @tools.cache(skiparg=3)
    def _get_checklist_by_model(self, cr, uid):
        res = {}
        ids = self.search(cr, SUPERUSER_ID, [], context={'active_test': True})
        for checklist in self.browse(cr, SUPERUSER_ID, ids):
            res[checklist.model] = checklist.id
        return res

    @staticmethod
    def _get_checklist_task_inst(self):
        domain = [('task_id.checklist_id.model_id.model', '=', self._name), ('res_id', '=', self.id)]
        self.checklist_task_instance_ids = self.env['checklist.task.instance'].search(domain)

    @api.model
    def _patch_model_decoration(self, model):
        model_obj = self.env[model].sudo()
        if 'checklist_task_instance_ids' in model_obj._fields:
            return False
        cls = type(model_obj).__base__
        update = not hasattr(cls, '_get_checklist_task_inst')
        setattr(cls, '_get_checklist_task_inst', api.one(Checklist._get_checklist_task_inst))
        new_fields = {
            'checklist_task_instance_ids': fields.One2many('checklist.task.instance',
                                                           string='Checklist Task Instances',
                                                           compute='_get_checklist_task_inst'),
            'total_progress_rate': fields.Float('Progress Rate', digits=(16, 2)),
            'total_progress_rate_mandatory': fields.Float('Mandatory Progress Rate', digits=(16, 2)),
        }
        for new_field in new_fields.iteritems():
            setattr(type(model_obj), *new_field)
            model_obj._add_field(*new_field)
        model_obj._setup_base(partial=not self.pool.ready)
        model_obj._setup_fields()
        model_obj._setup_complete()
        model_obj._auto_init()
        model_obj._auto_end()
        if update:
            for method in ('create', 'write', 'fields_view_get'):
                cls._patch_method(method, getattr(checklist_decorators, 'checklist_%s_decorator' % method)())
        return update

    @api.model
    def _revert_model_decoration(self, model):
        update = False
        model_obj = self.env[model].sudo()
        for method_name in ('create', 'write', 'fields_view_get'):
            method = getattr(model_obj, method_name)
            while hasattr(method, 'origin'):
                if method.__name__ == 'checklist_wrapper':
                    model_obj._revert_method(method_name)
                    update = True
                    break
                method = method.origin
        return update

    @api.model
    def _update_models(self, models=None):
        update = False
        if not models:
            models = dict([(checklist.model_id, checklist) for checklist in self.with_context(active_test=True).search([])])
        for model, checklist in models.iteritems():
            if model.model not in self.env.registry.models:
                continue
            if checklist:
                update |= self._patch_model_decoration(model.model)
            else:
                update |= self._revert_model_decoration(model.model)
        if update:
            if self.pool.ready:
                RegistryManager.signal_registry_change(self._cr.dbname)
            self.clear_caches()

    def __init__(self, pool, cr):
        super(Checklist, self).__init__(pool, cr)
        setattr(Registry, 'setup_models', update_checklists(getattr(Registry, 'setup_models')))

    @api.model
    def create(self, vals):
        checklist = super(Checklist, self).create(vals)
        self._update_models({self.env['ir.model'].browse(vals['model_id']): checklist})
        return checklist

    @api.multi
    def write(self, vals):
        if 'model_id' in vals or 'active' in vals:
            models = {}.fromkeys(self.mapped('model_id'), False)
            if vals.get('model_id'):
                models.update({self.env['ir.model'].browse(vals['model_id']): self})
        result = super(Checklist, self).write(vals)
        if 'model_id' in vals or 'active' in vals:
            self._update_models(models)
        return result

    @api.multi
    def unlink(self):
        models = dict([(checklist.model_id, False) for checklist in self])
        result = super(Checklist, self).unlink()
        self._update_models(models)
        return result

    @api.one
    def compute_progress_rates(self, records=None):
        if self._context.get('do_no_compute_progress_rates'):
            return
        if not records:
            records = self.env[self.model].with_context(active_test=False).search([])
        for record in records.with_context(active_test=True, no_checklist=True):
            ctx = {'active_id': record.id, 'active_ids': [record.id], 'active_model': self.model}
            for task_inst in record.checklist_task_instance_ids:
                old_progress_rate = task_inst.progress_rate
                if task_inst.task_id.field_ids:
                    task_inst.progress_rate = 100.0 * len(task_inst.field_ids_filled) / len(task_inst.task_id.field_ids)
                else:
                    task_inst.progress_rate = 100.0
                if task_inst.task_id.action_id and old_progress_rate != task_inst.progress_rate == 100.0:
                    task_inst.task_id.action_id.with_context(**ctx).run()
            total_progress_rate = 0.0
            if record.checklist_task_instance_ids:
                total_progress_rate = sum(i.progress_rate for i in record.checklist_task_instance_ids) \
                    / len(record.checklist_task_instance_ids)
            vals = {'total_progress_rate': total_progress_rate}
            if self.active_field:
                total_progress_rate_mandatory = 100.0
                mandatory_inst = [i for i in record.checklist_task_instance_ids if i.mandatory]
                if mandatory_inst:
                    total_progress_rate_mandatory = sum(i.progress_rate for i in record.checklist_task_instance_ids if i.mandatory) \
                        / len(mandatory_inst)
                vals['total_progress_rate_mandatory'] = total_progress_rate_mandatory
                vals['active'] = total_progress_rate_mandatory == 100.0
            old_total_progress_rate = record.total_progress_rate
            record.write(vals)
            if self.action_id and old_total_progress_rate != record.total_progress_rate == 100.0:
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

    @api.one
    def _manage_task_instances(self, records=None):
        if records:
            records = records.sudo()
        else:
            records = self.env[self.model_id.model].sudo().with_context(active_test=False).search([])
        for record in records.with_context(active_test=False):
            condition_checked = eval(self.condition, {'object': record, 'time': time})
            task_inst = record.checklist_task_instance_ids.filtered(lambda i: i.task_id == self)
            if condition_checked and not task_inst:
                task_inst.create({'task_id': self.id, 'res_id': record.id})
            elif not condition_checked and task_inst:
                task_inst.unlink()
            record.checklist_task_instance_ids.invalidate_cache()  # Force invalidate cache required because of a bug?
            if record.checklist_task_instance_ids:
                record.checklist_task_instance_ids[0].checklist_id.compute_progress_rates(record.with_context(checklist_computation=True))

    @api.model
    def create(self, vals):
        task = super(ChecklistTask, self).create(vals)
        self._manage_task_instances()
        return task

    @api.multi
    def write(self, vals):
        checklists = set([task.checklist_id for task in self])
        result = super(ChecklistTask, self).write(vals)
        self._manage_task_instances()
        for checklist in checklists:  # Recompute only previous ones because new ones are recomputed in _manage_task_instances
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
    model_id = fields.Many2one('ir.model', 'Model', related='task_id.checklist_id.model_id')
    name = fields.Char(size=128, related='task_id.name')
    mandatory = fields.Boolean('Required to make record active', related='task_id.mandatory')
    res_id = fields.Integer('Resource ID', index=True, required=True)
    active = fields.Boolean(compute='_get_activity', search='_search_activity')
    field_ids_to_fill = fields.One2many('checklist.task.field', string='Fields to fill', compute='_get_activity')
    field_ids_filled = fields.One2many('checklist.task.field', string='Filled fields', compute='_get_activity')
    progress_rate = fields.Float('Progress Rate', digits=(16, 2), default=0.0)

    @api.one
    @api.depends()
    def _get_activity(self):
        self.active = self.task_id.active
        field_ids_to_fill = self.env['checklist.task.field'].browse()
        field_ids_filled = self.env['checklist.task.field'].browse()
        localdict = {'object': self.env[self.model_id.model].browse(self.res_id),
                     'time': time}
        if eval(self.task_id.condition, localdict):
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

    def _search_activity(self, operator, value):
        # TODO: manage task condition
        return [('task_id.active', operator, value)]
