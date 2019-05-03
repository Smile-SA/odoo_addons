# -*- coding: utf-8 -*-
# (C) 2011 Smile (<http://www.smile.fr>)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from collections import defaultdict
from lxml import etree

from odoo import api, fields, models, tools, _
from odoo.exceptions import ValidationError


class Checklist(models.Model):
    _name = 'checklist'
    _description = 'Checklist'

    name = fields.Char(required=True, translate=True)
    active = fields.Boolean(default=True)
    model_id = fields.Many2one(
        'ir.model', 'Model', required=True, auto_join=True)
    task_ids = fields.One2many(
        'checklist.task', 'checklist_id', 'Tasks')
    active_field = fields.Boolean(
        "Has an 'Active' field", compute='_get_active_field')

    action_id = fields.Many2one(
        'ir.actions.server', 'Action',
        help='Run when checklist becomes complete')
    act_window_ids = fields.Many2many(
        'ir.actions.act_window', 'checklist_act_window_rel',
        'act_window_id', 'checklist_id', 'Menus')
    view_ids = fields.Many2many(
        'ir.ui.view', 'checklist_view_rel',
        'view_id', 'checklist_id', 'Views')
    model = fields.Char(related='model_id.model')

    @api.one
    def _get_active_field(self):
        if self.model_id:
            self.active_field = \
                'active' in self.env[self.model_id.model]._fields

    @api.one
    @api.constrains('model_id')
    def _check_unique_checklist_per_model(self):
        self = self.with_context(active_test=True)
        domain = [('model_id', '=', self.model_id.id), ('id', '!=', self.id)]
        if self.search_count(domain):
            raise ValidationError(
                _('A checklist already exists for this model!'))

    @api.model
    @tools.ormcache()
    def _get_checklist_by_model(self):
        res = {}
        for checklist in self.with_context(active_test=True).sudo().search([]):
            res[checklist.model] = checklist.id
        return res

    @api.one
    def _compute_progress_rates(self, records=None):
        if not self._context.get('do_not_compute_progress_rates'):
            if not records:
                records = self.env[self.model].sudo(). \
                    with_context(active_test=False).search([])
            for record in records.with_context(active_test=True):
                vals = self._get_record_vals(record)
                if vals:
                    old_progress_rate = record.x_checklist_progress_rate
                    record.write(vals)
                    if self.action_id and old_progress_rate != \
                            record.x_checklist_progress_rate == 100.0:
                        ctx = {
                            'active_id': record.id,
                            'active_ids': [record.id],
                            'active_model': self.model_id.model,
                        }
                        self.action_id.with_context(**ctx).run()

    @api.multi
    def _get_record_vals(self, record):
        def compute_progress_rate(task_insts):
            if not task_insts:
                return 0.0
            return 100.0 * len(task_insts.filtered(
                lambda inst: inst.complete)) / len(task_insts)

        self.ensure_one()
        task_insts = self.env['checklist.task.instance'].search([
            ('task_id.checklist_id', '=', self.id),
            ('res_id', '=', record.id),
        ])
        if not task_insts:
            return {}
        for task_inst in task_insts:
            task_inst.complete = bool(record.filtered_from_domain(
                task_inst.task_id.complete_domain))
        vals = {'x_checklist_progress_rate':
                compute_progress_rate(task_insts)}
        if self.active_field:
            task_insts = task_insts.filtered(lambda inst: inst.mandatory)
            if task_insts:
                vals['x_checklist_progress_rate_mandatory'] = \
                    compute_progress_rate(task_insts)
                vals['active'] = \
                    vals['x_checklist_progress_rate_mandatory'] == 100.0
        return vals

    @api.model_cr
    def _register_hook(self):

        def make_create():
            @api.model
            def create(self, vals, **kw):
                record = create.origin(self, vals, **kw)
                record._manage_checklist_task_instances()
                return record
            return create

        def make_write():
            @api.multi
            def _write(self, vals, **kw):
                _write.origin(self, vals, **kw)
                self._manage_checklist_task_instances()
                return True
            return _write

        def make_fields_view_get():
            @api.model
            def fields_view_get(self, view_id=None, view_type='form',
                                toolbar=False, submenu=False, **kw):
                res = fields_view_get.origin(self, view_id, view_type,
                                             toolbar, submenu, **kw)
                self.env['checklist']._complete_view(
                    self._name, view_type, view_id, res)
                return res
            return fields_view_get

        patched_models = defaultdict(set)

        def patch(model, name, method):
            if model not in patched_models[name]:
                patched_models[name].add(model)
                model._patch_method(name, method)

        for checklist in self.with_context({}).search([]):
            Model = self.env.get(checklist.model_id.model)
            patch(Model, 'create', make_create())
            patch(Model, '_write', make_write())
            patch(Model, 'fields_view_get', make_fields_view_get())

    @api.model
    def _complete_view(self, model, view_type, view_id, res):
        checklist_id = self._get_checklist_by_model().get(model)
        if not checklist_id:
            return
        checklist = self.browse(checklist_id).read(
            ['name', 'act_window_ids', 'view_ids'], load='_classic_write')[0]
        if checklist['act_window_ids'] and \
                self._context.get('act_window_id') and \
                self._context['act_window_id'] not in \
                checklist['act_window_ids']:
            return
        if checklist['view_ids'] and \
                res['view_id'] not in checklist['view_ids']:
            return
        if not self._context.get('no_checklist') and \
                view_type in ('tree', 'form'):
            if view_type == 'tree':
                arch = res['arch']
                idx = arch.rfind('<')
                res['arch'] = ''.join([
                    arch[:idx],
                    """<field name="x_checklist_progress_rate"
                        readonly="1" widget="progressbar"/>""",
                    arch[idx:],
                ])
                res['fields'].update(self.env[model].fields_get(
                    ['x_checklist_progress_rate']))
            elif view_type == 'form':
                root = etree.XML(res['arch'])
                button_box = root.find(".//div[@class='oe_button_box']")
                if button_box is None:
                    button_box = etree.Element(
                        'div', attrib={'class': 'oe_button_box'})
                    sheet = root.find("sheet")
                    if not sheet:
                        sheet = etree.Element('sheet')
                        for child in root.getchildren()[::-1]:
                            sheet.insert(0, child)
                        root.insert(0, sheet)
                    sheet.insert(0, button_box)
                button_box.insert(0, etree.XML("""
                <button class="oe_stat_button"
                    type="object" name="open_checklist"
                    attrs="{'invisible':
                      [('x_checklist_task_instance_ids', '=', [])]}">
                  <field string="%s" name="x_checklist_progress_rate"
                    widget="percentpie"/>
                  <field name="x_checklist_task_instance_ids" invisible="1"/>
                </button>
                """ % (checklist['name'],)))
                res['arch'], res['fields'] = self.env['ir.ui.view']. \
                    postprocess_and_fields(model, root, view_id)

    @api.model
    def create(self, vals):
        self = self
        checklist = super(Checklist, self.with_context(
            do_not_compute_progress_rates=True)).create(vals)
        self.clear_caches()
        checklist.with_context(
            do_not_compute_progress_rates=False)._compute_progress_rates()
        return checklist

    @api.multi
    def write(self, vals):
        if 'task_ids' in vals:
            checklists_to_recompute = self
        elif 'model_id' in vals:
            checklists_to_recompute = self.filtered(
                lambda checklist: checklist.model_id.id != vals['model_id'])
        else:
            checklists_to_recompute = self.browse()
        res = super(Checklist, self.with_context(
            do_not_compute_progress_rates=True)).write(vals)
        self.clear_caches()
        if 'model_id' in vals:
            checklists_to_recompute.mapped('task_ids').with_context(
                do_not_compute_progress_rates=True)._manage_task_instances()
        checklists_to_recompute._compute_progress_rates()
        return res

    @api.multi
    def unlink(self):
        res = super(Checklist, self).unlink()
        self.clear_caches()
        return res

    @api.one
    def _update_models(self):
        Field = self.env['ir.model.fields']
        domain = [
            ('model_id', '=', self.model_id.id),
            ('name', '=', 'x_checklist_task_instance_ids')
        ]
        if not Field.search_count(domain):
            new_fields = [
                {
                    'name': 'x_checklist_task_instance_ids',
                    'field_description': 'Checklist',
                    'ttype': 'many2many',
                    'relation': 'checklist.task.instance',
                    'compute': 'self._get_checklist_task_instances()',
                    'readonly': True,
                    'store': False,
                }, {
                    'name': 'x_checklist_progress_rate',
                    'field_description': 'Progress Rate',
                    'ttype': 'float',
                    'readonly': True,
                }, {
                    'name': 'x_checklist_progress_rate_mandatory',
                    'field_description': 'Mandatory Progress Rate',
                    'ttype': 'float',
                    'readonly': True,
                },
            ]
            for vals in new_fields:
                vals['model_id'] = self.model_id.id
                Field.create(vals)
