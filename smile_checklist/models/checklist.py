# -*- coding: utf-8 -*-

from odoo import api, fields, models, SUPERUSER_ID, tools, _
from odoo.exceptions import ValidationError
from odoo.modules.registry import Registry, RegistryManager

import checklist_decorators


def update_checklists(method):
    def wrapper(self, cr, *args, **kwargs):
        res = method(self, cr, *args, **kwargs)
        if self.get('checklist'):
            cr.execute("select relname from pg_class where relname='checklist'")
            if cr.rowcount:
                env = api.Environment(cr, SUPERUSER_ID, {})
                env['checklist']._update_models()
        return res
    return wrapper


class Checklist(models.Model):
    _name = 'checklist'
    _description = 'Checklist'

    def __init__(self, pool, cr):
        super(Checklist, self).__init__(pool, cr)
        setattr(Registry, 'setup_models', update_checklists(getattr(Registry, 'setup_models')))

    name = fields.Char(size=128, required=True, translate=True)
    model_id = fields.Many2one('ir.model', 'Model', required=True)
    model = fields.Char(related='model_id.model', readonly=True)
    active = fields.Boolean('Active', default=True)
    active_field = fields.Boolean("Has an 'Active' field", compute='_get_active_field')
    action_id = fields.Many2one('ir.actions.server', 'Action')
    act_window_ids = fields.Many2many('ir.actions.act_window', 'checklist_act_window_rel', 'act_window_id', 'checklist_id', 'Menus')
    view_ids = fields.Many2many('ir.ui.view', 'checklist_view_rel', 'view_id', 'checklist_id', 'Views')
    task_ids = fields.One2many('checklist.task', 'checklist_id', 'Tasks')

    @api.one
    def _get_active_field(self):
        if self.model_id:
            self.active_field = 'active' in self.env[self.model_id.model]._fields

    @api.one
    @api.constrains('model_id')
    def _check_unique_checklist_per_object(self):
        self = self.with_context(active_test=True)
        domain = [('model_id', '=', self.model_id.id), ('id', '!=', self.id)]
        if self.search_count(domain):
            raise ValidationError(_('A checklist already exists for this model !'))

    @api.model
    @tools.ormcache()
    def _get_checklist_by_model(self):
        res = {}
        for checklist in self.with_context(active_test=True).sudo().search([]):
            res[checklist.model] = checklist.id
        return res

    @staticmethod
    def _get_checklist_task_inst(self):
        domain = [('task_id.checklist_id.model_id.model', '=', self._name), ('res_id', '=', self.id)]
        self.checklist_task_instance_ids = self.env['checklist.task.instance'].search(domain)

    @api.model
    def _patch_model_decoration(self, model):
        context = dict(self._context, todo=[])
        model_obj = self.env[model].with_context(**context).sudo()
        if 'checklist_task_instance_ids' in model_obj._fields:
            return False
        update = not hasattr(model_obj, '_get_checklist_task_inst')
        if update:
            setattr(type(model_obj), '_get_checklist_task_inst',
                    api.one(Checklist._get_checklist_task_inst))
        new_fields = {
            'checklist_task_instance_ids': fields.One2many('checklist.task.instance',
                                                           string='Checklist Task Instances',
                                                           compute='_get_checklist_task_inst'),
            'total_progress_rate': fields.Float('Progress Rate', digits=(16, 2)),
            'total_progress_rate_mandatory': fields.Float('Mandatory Progress Rate', digits=(16, 2)),
        }
        for new_field in new_fields.iteritems():
            model_obj._add_field(*new_field)
        partial = not self.pool.ready
        model_obj._setup_base(partial=partial)
        model_obj._setup_fields(partial=partial)
        model_obj._setup_complete()
        model_obj._auto_init()
        model_obj.init()
        model_obj._auto_end()
        if update:
            for method in ('create', 'write', 'fields_view_get'):
                decorated_method = getattr(checklist_decorators, 'checklist_%s_decorator' % method)()
                model_obj._patch_method(method, decorated_method)
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
            checklists = self.with_context(active_test=True).search([])
            models = {checklist.model_id: checklist for checklist in checklists}
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
                    task_inst.progress_rate = 100.0 * len(task_inst.field_ids_filled) \
                        / len(task_inst.task_id.field_ids)
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
