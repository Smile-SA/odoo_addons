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
            checklist = checklist_obj.browse(checklist_id).read(['act_window_ids', 'view_ids'], load='_classic_write')[0]
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
                fields_view['fields']['total_progress_rate'] = {'string': 'Progress Rate', 'type': 'float', 'context': {}}
                if view_type == 'tree':
                    arch_list.append(arch[:arch.rfind('<')])
                    arch_list.append("""<field name="total_progress_rate" readonly="1" widget="progressbar"/>""")
                    arch_list.append(arch[arch.rfind('<'):])
                    fields_view['arch'] = ''.join(arch_list)
                if view_type == 'form':
                    fields_view['fields'].update(self.fields_get(['checklist_task_instance_ids']))
                    fields_view['fields']['checklist_task_instance_ids']['views'] = {}

                    gnode1 = etree.Element('div', attrib={'style': "float: left; margin-left: -16px; min-width: 80%;"})
                    gnode2 = etree.Element('div', attrib={'style': "float: right; padding-left: 4px; max-width: 20%;",
                                                          'attrs': "{'invisible': [('checklist_task_instance_ids', '=', [])]}"})
                    gnode2.insert(0, etree.XML("""<group col="1">
                        <separator string="Checklist"/>
                        <field name="total_progress_rate" nolabel="1"  readonly="1" widget="progressbar"/>
                        <field name="checklist_task_instance_ids" nolabel="1"  readonly="1" context="{'active_test': True}"/>
                    </group>"""))

                    index_add = 0
                    snode = etree.XML(fields_view['arch'])
                    if snode.find('sheet'):
                        sheet_index = 0
                        for index, child in enumerate(snode.getchildren()):
                            if child.tag == 'sheet' or (child.tag == 'div' and child.attrib.get('class') == 'oe_chatter'):
                                if child.tag == 'sheet':
                                    sheet_index = index
                                gnode1.insert(index - sheet_index, child)
                                snode.insert(index, gnode1)
                                index_add = 1
                            else:
                                index += index_add
                                snode.insert(index, child)
                        snode.insert(sheet_index, gnode2)
                    else:
                        for index, child in enumerate(snode.getchildren()):
                            gnode1.insert(index, child)
                        snode.insert(0, gnode1)
                        snode.insert(0, gnode2)
                    xarch, _ = self.env['ir.ui.view'].postprocess_and_fields(self._name, snode, view_id)
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
