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


def checklist_view_decorator():
    def checklist_wrapper(self, cr, uid, view_id=None, view_type='form', context=None, toolbar=False, submenu=False):
        fields_view = checklist_wrapper.origin(self, cr, uid, view_id, view_type, context, toolbar, submenu)
        context = context or {}
        checklist_obj = self.pool.get('checklist')
        if checklist_obj and hasattr(checklist_obj, '_get_checklist_by_model'):
            checklist_id = checklist_obj._get_checklist_by_model(cr, uid).get(self._name)
            if not checklist_id:
                return fields_view
            checklist = checklist_obj.read(cr, uid, checklist_id, ['view_ids'])
            if not view_id:
                cr.execute("""SELECT id FROM ir_ui_view
                              WHERE model=%s AND type=%s AND inherit_id IS NULL
                              ORDER BY priority LIMIT 1""", (self._name, view_type))
                view_id = cr.fetchone()
                view_id = view_id and view_id[0] or False
            if not checklist['view_ids'] or view_id in checklist['view_ids'] or not context.get('no_checklist'):
                arch = fields_view['arch']
                arch_list = []
                fields_view['fields']['total_progress_rate'] = {'string': 'Progress Rate', 'type': 'float', 'context': {}}
                if view_type == 'tree':
                    arch_list.append(arch[:arch.rfind('<')])
                    arch_list.append("""<field name="total_progress_rate" readonly="1" widget="progressbar"/>""")
                    arch_list.append(arch[arch.rfind('<'):])
                    fields_view['arch'] = ''.join(arch_list)
                if view_type == 'form':
                    fields_view['fields']['checklist_task_instance_ids'] = {'string': 'Tasks', 'type': 'one2many',
                                                                            'relation': 'checklist.task.instance', 'context': {},
                                                                            'readonly': True}
                    doc = etree.XML(fields_view['arch'])
                    snode = doc
                    has_sheet = False
                    if doc.findall('sheet'):
                        has_sheet = True
                        snode = doc.find('sheet')
                    gnode = etree.Element('group', attrib={'colspan': '1', 'col': '4'})
                    gnode1 = etree.Element('group', attrib={'colspan': '3', 'col': '1'})
                    for index, children in enumerate(snode.getchildren()):
                        gnode1.insert(index, children)
                    gnode.insert(0, gnode1)
                    gnode2 = etree.Element('group', attrib={'colspan': '1', 'col': '2'})
                    gnode2.insert(0, etree.XML("""<group col="1"><separator string="Checklist"/>
                        <field name="total_progress_rate" nolabel="1" readonly="1" widget="progressbar"/>
                        <field name="checklist_task_instance_ids" nolabel="1" context="{'active_test': True}"/>
                    </group>"""))
                    gnode.insert(1, gnode2)
                    snode.insert(0, gnode)
                    if has_sheet:
                        index = 0
                        if doc.findall('header'):
                            index = 1
                        doc.insert(index, snode)
                    fields_view['arch'] = etree.tostring(doc)
        return fields_view
    return checklist_wrapper


def checklist_create_decorator():
    @api.model
    def checklist_wrapper(self, vals):
        record = checklist_wrapper.origin(self, vals)
        if 'checklist_task_instance_ids' in self._fields:
            record.checklist_task_instance_ids[0].checklist_id.compute_progress_rates([record.id])
        return record
    return checklist_wrapper


def checklist_write_decorator():
    @api.multi
    def checklist_wrapper(self, vals):
        result = checklist_wrapper.origin(self, vals)
        if not self._context.get('no_checklist') and 'checklist_task_instance_ids' in self._fields:
            self.with_context(no_checklist=True).checklist_task_instance_ids[0].checklist_id.compute_progress_rates(self.ids)
        return result
    return checklist_wrapper
