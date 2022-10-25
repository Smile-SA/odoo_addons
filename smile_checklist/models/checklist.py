# -*- coding: utf-8 -*-
# (C) 2020 Smile (<http://www.smile.fr>)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from collections import defaultdict
from lxml import etree

from odoo import api, fields, models, tools, _
from odoo.exceptions import ValidationError
from odoo.tools.safe_eval import safe_eval


class Checklist(models.Model):
    _name = 'checklist'
    _description = 'Checklist'

    name = fields.Char(required=True, translate=True)
    active = fields.Boolean(default=True)
    model_id = fields.Many2one('ir.model', 'Model', required=True, auto_join=True, ondelete='cascade')
    task_ids = fields.One2many('checklist.task', 'checklist_id', 'Tasks')
    active_field = fields.Boolean("Has an 'Active' field", compute='_get_active_field')
    action_id = fields.Many2one('ir.actions.server', 'Action', help='Run when checklist becomes complete')
    act_window_ids = fields.Many2many('ir.actions.act_window', 'checklist_act_window_rel',
                                      'act_window_id', 'checklist_id', 'Menus')
    view_ids = fields.Many2many('ir.ui.view', 'checklist_view_rel', 'view_id', 'checklist_id', 'Views')
    model = fields.Char('Model Name', related='model_id.model')

    def _get_active_field(self):
        for rec in self:
            if rec.model_id:
                rec.active_field = 'active' in self.env[rec.model_id.model]._fields

    @api.constrains('model_id')
    def _check_unique_checklist_per_model(self):
        for checklist in self:
            checklist = checklist.with_context(active_test=True)
            domain = [('model_id', '=', checklist.model_id.id), ('id', '!=', checklist.id)]
            if checklist.search_count(domain):
                raise ValidationError(_('A checklist already exists for this model!'))

    @api.model
    @tools.ormcache()
    def _get_checklist_by_model(self):
        res = {}
        for checklist in self.with_context(active_test=True).sudo().search([]):
            res[checklist.model] = checklist.id
        return res

    def _compute_progress_rates(self, records=None):
        for checklist in self:
            if not checklist._context.get('do_not_compute_progress_rates'):
                if not records:
                    records = self.env[checklist.model].sudo().with_context(active_test=False).search([])
                for record in records.with_context(active_test=True):
                    vals = checklist._get_record_vals(record)
                    if vals:
                        old_progress_rate = record.x_checklist_progress_rate
                        record.write(vals)
                        if checklist.action_id and old_progress_rate != record.x_checklist_progress_rate == 100.0:
                            ctx = {
                                'active_id': record.id,
                                'active_ids': [record.id],
                                'active_model': checklist.model_id.model,
                            }
                            checklist.action_id.with_context(**ctx).run()

    def _get_record_vals(self, record):
        def compute_progress_rate(task_insts):
            if not task_insts:
                return 0.0
            return round(100.0 * (len(task_insts.filtered(lambda inst: inst.complete)) / len(task_insts)), 0)

        self.ensure_one()
        task_insts = self.env['checklist.task.instance'].search([
            ('task_id.checklist_id', '=', self.id),
            ('res_id', '=', record.id),
        ])
        if not task_insts:
            return {}
        for task_inst in task_insts:
            task_inst.complete = bool(record.filtered_domain(safe_eval(task_inst.task_id.complete_domain)))
        vals = {'x_checklist_progress_rate': compute_progress_rate(task_insts)}
        if self.active_field:
            task_insts = task_insts.filtered(lambda inst: inst.mandatory)
            if task_insts:
                vals['x_checklist_progress_rate_mandatory'] = compute_progress_rate(task_insts)
                vals['active'] = vals['x_checklist_progress_rate_mandatory'] == 100.0
        return vals

    def _register_hook(self):

        def make_create():
            @api.model
            def create(self, vals, **kw):
                record = create.origin(self, vals, **kw)
                record._manage_checklist_task_instances()
                return record

            return create

        def make_write():
            def write(self, vals, **kw):
                write.origin(self, vals, **kw)
                self._manage_checklist_task_instances()
                return True

            return write

        def make_fields_view_get():
            @api.model
            def get_view(self, view_id=None, view_type='form', **options):
                res = get_view.origin(self, view_id, view_type=view_type, **options)
                self.env['checklist']._complete_view(self._name, view_type, res)
                return res

            return get_view

        patched_models = defaultdict(set)

        def patch(model, name, method):
            if model not in patched_models[name]:
                patched_models[name].add(model)
                model._patch_method(name, method)

        for checklist in self.search([('name', '!=', False), ('model_id', '!=', False)]):
            Model = self.env.get(checklist.model_id.model)
            patch(Model, 'create', make_create())
            patch(Model, 'write', make_write())
            patch(Model, 'get_view', make_fields_view_get())

    @api.model
    def _complete_view(self, model, view_type, res):
        checklist_id = self._get_checklist_by_model().get(model)
        if not checklist_id:
            return
        checklist = self.browse(checklist_id).read(['name', 'act_window_ids', 'view_ids'], load='_classic_write')[0]
        if checklist['act_window_ids'] and self._context.get('act_window_id') and \
            self._context['act_window_id'] not in checklist['act_window_ids']:
            return
        if checklist['view_ids'] and res['view_id'] not in checklist['view_ids']:
            return
        if not self._context.get('no_checklist') and view_type in ('tree', 'form'):
            if view_type == 'tree' and model == res.get('model'):
                arch = res['arch']
                if etree.XML(res['arch']).find(".//field[@name='x_checklist_progress_rate']") is None:
                    idx = arch.rfind('<')
                    res['arch'] = ''.join([
                        arch[:idx],
                        """<field name="x_checklist_progress_rate" string="%s"
                            readonly="1" widget="progressbar"/>""" % _(
                            "Progress Rate"),
                        arch[idx:],
                    ])
            elif view_type == 'form' and model == res.get('model'):
                root = etree.XML(res['arch'])
                # root = etree.fromstring(
                #     res['arch'],
                #     parser=etree.XMLParser(encoding='utf-8', remove_blank_text=True))
                if root.find(".//button[@name='open_checklist']") is None:
                    button_box = root.find(".//div[@name='button_box']")
                    if button_box is None:
                        button_box = etree.Element('div', attrib={'class': 'button_box'})
                        sheet = root.find("sheet")
                        if not sheet:
                            sheet = etree.Element('sheet')
                            for child in root.getchildren()[::-1]:
                                sheet.insert(0, child)
                            root.insert(0, sheet)
                        sheet.insert(0, button_box)
                    button_box.insert(0, etree.XML("""
                    <button class="o_button_icon oe_stat_button"
                        type="object" name="open_checklist"
                        modifiers="{&quot;invisible&quot;: &quot;[('x_checklist_task_instance_ids', '=', [])]&quot;}">
                        <div class="o_form_field o_stat_info">
                            <span class="o_stat_value">
                              <field name="x_checklist_progress_rate" string=" " class="o_button_icon"
                              widget="percentpie" nolabel="1"/></span>
                           </div> <span class="o_stat_text" title="%s">%s</span>
                        <field name="x_checklist_task_instance_ids" modifiers="{&quot;invisible&quot;: true}" />
                    </button>
                    """ % (checklist['name'], checklist['name'])))
                    res['arch'] = etree.tostring(root, pretty_print=True, encoding="unicode").replace('\t', '')

    @api.model_create_multi
    def create(self, vals):
        self = self
        checklist = super(Checklist, self.with_context(do_not_compute_progress_rates=True)).create(vals)
        self.clear_caches()
        checklist.with_context(do_not_compute_progress_rates=False)._compute_progress_rates()
        return checklist

    def write(self, vals):
        if 'task_ids' in vals:
            checklists_to_recompute = self
        elif 'model_id' in vals:
            checklists_to_recompute = self.filtered(lambda checklist: checklist.model_id.id != vals['model_id'])
        else:
            checklists_to_recompute = self.browse()
        res = super(Checklist, self.with_context(do_not_compute_progress_rates=True)).write(vals)
        self.clear_caches()
        if 'model_id' in vals:
            checklists_to_recompute.mapped('task_ids').with_context(
                do_not_compute_progress_rates=True)._manage_task_instances()
        checklists_to_recompute.with_context(do_not_compute_progress_rates=False)._compute_progress_rates()
        return res

    def unlink(self):
        res = super(Checklist, self).unlink()
        self.clear_caches()
        return res

    def _update_models(self):
        for rec in self:
            Field = self.env['ir.model.fields']
            domain = [
                ('model_id', '=', rec.model_id.id),
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
                    },
                    {
                        'name': 'x_checklist_progress_rate',
                        'field_description': 'Progress Rate',
                        'ttype': 'float',
                        'readonly': True,
                    },
                    {
                        'name': 'x_checklist_progress_rate_mandatory',
                        'field_description': 'Mandatory Progress Rate',
                        'ttype': 'float',
                        'readonly': True,
                    },
                ]
                for vals in new_fields:
                    vals['model_id'] = rec.model_id.id
                    Field.create(vals)
