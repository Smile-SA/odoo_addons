# -*- coding: utf-8 -*-

from lxml import etree

from openerp import api


def checklist_fields_view_get_decorator():
    @api.model
    def checklist_wrapper(self, view_id=None, view_type='form', toolbar=False, submenu=False):
        fields_view = checklist_wrapper.origin(self, view_id, view_type, toolbar, submenu)
        checklist_obj = self.env['checklist']
        if hasattr(checklist_obj, '_get_checklist_by_model'):
            checklist_id = checklist_obj._get_checklist_by_model(self._cr, self._uid).get(self._name)
            if not checklist_id:
                return fields_view
            checklist = checklist_obj.browse(checklist_id).read(['name', 'act_window_ids', 'view_ids'],
                                                                load='_classic_write')[0]
            if checklist['act_window_ids'] and self._context.get('act_window_id') and \
                    self._context['act_window_id'] not in checklist['act_window_ids']:
                return fields_view
            if not view_id:
                self._cr.execute("""SELECT id FROM ir_ui_view
                                    WHERE model=%s AND type=%s AND inherit_id IS NULL
                                    ORDER BY priority LIMIT 1""", (self._name, view_type))
                view_id = self._cr.fetchone()
                view_id = view_id and view_id[0] or False
            if checklist['view_ids'] and view_id not in checklist['view_ids']:
                return fields_view
            if not self._context.get('no_checklist'):
                arch = fields_view['arch']
                arch_list = []
                fields_view['fields'].update(self.fields_get(['total_progress_rate']))
                if view_type == 'tree':
                    arch_list.append(arch[:arch.rfind('<')])
                    arch_list.append("""<field name="total_progress_rate" readonly="1" widget="progressbar"/>""")
                    arch_list.append(arch[arch.rfind('<'):])
                    fields_view['arch'] = ''.join(arch_list)
                if view_type == 'form':
                    root = etree.XML(fields_view['arch'])
                    button_box = root.find(".//div[@class='oe_button_box']")
                    if button_box is None:
                        button_box = etree.Element('div', attrib={'class': 'oe_button_box'})
                        sheet = root.find("sheet")
                        if not sheet:
                            sheet = etree.Element('sheet')
                            for child in root.getchildren()[::-1]:
                                sheet.insert(0, child)
                            root.insert(0, sheet)
                        sheet.insert(0, button_box)
                    button_box.insert(0, etree.XML("""<button class="oe_stat_button" type="action" name="%d">
                        <field string="%s" name="total_progress_rate" widget="percentpie"/>
                    </button>""" % (self.env.ref('smile_checklist.action_checklist_task_instance').id, checklist['name'])))
                    xarch, _ = self.env['ir.ui.view'].postprocess_and_fields(self._name, root, view_id)
                    fields_view['arch'] = xarch
        return fields_view
    return checklist_wrapper


def checklist_create_decorator():
    @api.model
    def checklist_wrapper(self, vals):
        record = checklist_wrapper.origin(self, vals)
        record._manage_checklist_task_instances()
        return record
    return checklist_wrapper


def checklist_write_decorator():
    @api.multi
    def checklist_wrapper(self, vals):
        result = checklist_wrapper.origin(self, vals)
        self._manage_checklist_task_instances()
        return result
    return checklist_wrapper
