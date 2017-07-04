# -*- coding: utf-8 -*-

from lxml import etree

from odoo import api


def checklist_fields_view_get_decorator():
    @api.model
    def checklist_wrapper(self, view_id=None, view_type='form', toolbar=False, submenu=False):
        res = checklist_wrapper.origin(self, view_id, view_type, toolbar, submenu)
        checklist_obj = self.env['checklist']
        if hasattr(checklist_obj, '_get_checklist_by_model'):
            checklist_id = checklist_obj._get_checklist_by_model().get(self._name)
            if not checklist_id:
                return res
            checklist = checklist_obj.browse(checklist_id).read(['name', 'act_window_ids', 'view_ids'],
                                                                load='_classic_write')[0]
            if checklist['act_window_ids'] and self._context.get('act_window_id') and \
                    self._context['act_window_id'] not in checklist['act_window_ids']:
                return res
            if checklist['view_ids'] and res['view_id'] not in checklist['view_ids']:
                return res
            if not self._context.get('no_checklist') and view_type in ('tree', 'form'):
                if view_type == 'tree':
                    arch = res['arch']
                    idx = arch.rfind('<')
                    res['arch'] = ''.join([
                        arch[:idx],
                        """<field name="total_progress_rate" readonly="1" widget="progressbar"/>""",
                        arch[idx:],
                    ])
                    res['fields'].update(self.fields_get(['total_progress_rate']))
                elif view_type == 'form':
                    root = etree.XML(res['arch'])
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
                    button_box.insert(0, etree.XML("""<button class="oe_stat_button"
                      type="object" name="open_checklist"
                      attrs="{'invisible': [('checklist_task_instance_ids', '=', [])]}">
                        <field string="%s" name="total_progress_rate" widget="percentpie"/>
                        <field name="checklist_task_instance_ids" invisible="1"/>
                    </button>""" % (checklist['name'],)))
                    res['arch'], res['fields'] = self.env['ir.ui.view'].postprocess_and_fields(self._name, root, view_id)
        return res
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
