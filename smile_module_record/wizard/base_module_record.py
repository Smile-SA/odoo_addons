# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2014 Smile (<http://www.smile.fr>).
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

import base64
import csv
from lxml import etree
import StringIO
import time
import zipfile

from openerp import api, fields, models, _


class BaseModuleRecord(models.TransientModel):
    _name = 'base.module.record'
    _description = "Base Module Record"

    state = fields.Selection([
        ('draft', 'Draft'),
        ('done', 'Done')
    ], readonly=True, default='draft')
    start_date = fields.Datetime('Records from', required=True, default=lambda *a: time.strftime('%Y-%m-%d %H:%M:%S'))
    date_filter = fields.Selection([
        ('create', 'created'),
        ('write', 'modified'),
        ('create_write', 'created or modified'),
    ], 'Records only', required=True, default='create_write')
    model_ids = fields.Many2many('ir.model', 'base_module_record_model_rel',
                                 'wizard_id', 'model_id', 'Objects',
                                 domain=[('osv_memory', '=', False)])
    file = fields.Binary(filename='filename', readonly=True)
    filename = fields.Char(size=64, required=True, default='data_module.zip')
    filetype = fields.Selection([
        ('csv', 'CSV'),
        ('xml', 'XML'),
    ], required=True, default='csv')

    def _get_models(self):
        models = self.model_ids
        if not models:
            models = [model for model in self.env['ir.model'].search([('osv_memory', '=', False)]) if self.env[model.model]._auto]
        return models

    def _get_domain(self):
        domain = []
        if 'create' in self.date_filter:
            domain.append(('create_date', '>=', self.start_date))
        if 'write' in self.date_filter:
            domain.append(('write_date', '>=', self.start_date))
        if self.date_filter == 'create_write':
            domain = ['|'] + domain
        return domain

    def _export_ir_properties(self, models, res_ids_by_model):
        if 'ir.property' in (model.model for model in models):
            return []
        property_obj = self.env['ir.property']
        properties = property_obj.browse()
        for model in models:
            res_ids = [False] + ['%s,%s' % (model, res_id) for res_id in res_ids_by_model[model.model]]
            properties |= property_obj.search([('fields_id.model_id', '=', model.id), ('res_id', 'in', res_ids)])
        if not properties:
            return []
        fields_to_export = property_obj.get_fields_to_export()
        rows = [fields_to_export]
        rows.extend(properties.export_data(fields_to_export)['datas'])
        return [('ir.property', rows)]

    def _export_data_by_model(self):
        models = self._get_models()
        datas = self.env['ir.model'].get_ordered_model_graph(models)
        domain = self._get_domain()
        res_ids_by_model = {}
        for index, (model, fields_to_export) in enumerate(datas):
            res_obj = self.env[model]
            recs = res_obj.search(res_obj._log_access and domain or [])
            if 'parent_left' in res_obj._fields:
                recs = recs.sorted(key=lambda rec: rec.parent_left)
            res_ids_by_model[model] = recs.ids
            rows = [fields_to_export]
            rows.extend(recs.export_data(fields_to_export)['datas'])
            datas[index] = (model, rows)
        datas.extend(self._export_ir_properties(models, res_ids_by_model))
        return datas

    def _convert_to_csv(self, model, rows):
        s = StringIO.StringIO()
        writer = csv.writer(s, quoting=csv.QUOTE_NONNUMERIC)
        for row in rows:
            for index, data in enumerate(row):
                if not data:
                    data = None
                if data is True:
                    data = 1
                if isinstance(data, basestring):
                    data = data.replace('\n', ' ').replace('\t', ' ')
                    try:
                        data = data.encode('utf-8')
                    except UnicodeError:
                        pass
                row[index] = data
            writer.writerow(row)
        return s.getvalue()

    def _convert_to_xml(self, model, rows):
        openerp_elem = etree.Element('openerp')
        data_elem = etree.SubElement(openerp_elem, 'data')
        data_elem.set('noupdate', '1')
        fields_ = rows[0]
        for row in rows[1:]:
            record_elem = etree.SubElement(data_elem, 'record')
            record_elem.set('model', model._name)
            record_elem.set('id', row[fields_.index('id')])
            for field_name in fields_:
                if field_name == 'id':
                    continue
                field_elem = etree.SubElement(record_elem, 'field')
                field_elem.set('name', field_name.replace(':id', ''))
                value = row[fields_.index(field_name)]
                field = model._fields[field_elem.get('name')]
                if isinstance(value, bool) or field.type == 'boolean':
                    field_elem.set('eval', '%s' % value)
                    continue
                if not field_name.endswith(':id'):
                    if field.type == 'selection':  # Contrary to CSV import, XML import requires key instead of value
                        for item in field._description_selection(self.env):
                            if item[1] == value:
                                field_elem.text = '%s' % item[0]
                    else:
                        field_elem.text = '%s' % value
                else:
                    if field.type == 'many2one':
                        field_elem.set(value and 'ref' or 'eval', value or 'False')
                    elif field.type == 'many2many':
                        field_elem.set('eval', '[(6, 0, %s)]' % map(lambda s: "ref('%s')" % s,
                                                                    (value or '').split(',')))
        return etree.tostring(openerp_elem, encoding='utf-8', xml_declaration=True)

    def _get_data_filecontent(self):
        data_files = []
        for model, rows in self._export_data_by_model():
            args = (self.env[model], rows)
            content = getattr(self, '_convert_to_%s' % self.filetype)(*args)
            content = content.replace('__export__.', '')
            data_files.append((model, content))
        return data_files

    @staticmethod
    def _get_data_filename(models, filetype):
        if filetype != 'csv':
            models = [model.replace('.', '_') for model in models]
        filenames = []
        for model in models:
            filename = 'data/%s.%s' % (model, filetype)
            if filename in filenames:
                filenames.append('data_addition/%s.%s' % (model, filetype))
            else:
                filenames.append(filename)
        return filenames

    def _get_dependencies(self):
        modules = []
        for model in self._get_models():
            modules.extend(model.modules.split(', '))
        return ', '.join(map(lambda mod: '"%s"' % mod, set(modules)))

    @property
    def openerp_filecontent(self):
        return """{
    "name" : "Data Module",
    "version" : "1.0",
    "author" : "Smile",
    "website" : "http://www.smile.fr",
    "description": "Data module created from smile_module_record",
    "category" : "Hidden",
    "depends" : [%(dependencies)s],
    "sequence": 20,
    "data" : [
        %(data_files)s,
    ],
    "test": [],
    "auto_install": False,
    "installable": True,
    "application": False,
}"""

    @api.one
    def create_module(self):
        datas = self._get_data_filecontent()
        models = [model for model, rows in datas]
        filenames = BaseModuleRecord._get_data_filename(models, self.filetype)
        zip_content = {
            '__init__.py': "#\n# Generated by smile_module_record\n#\n",
            '__openerp__.py': self.openerp_filecontent % {
                'dependencies': self._get_dependencies(),
                'data_files': ',\n        '.join(map(lambda model: '"%s"' % model, filenames)),
            },
        }
        for index, filename in enumerate(filenames):
            zip_content[filename] = datas[index][1]
        s = StringIO.StringIO()
        zip = zipfile.ZipFile(s, 'w')
        for filename, filecontent in zip_content.iteritems():
            info = zipfile.ZipInfo(filename)
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 2175008768  # specifies mode 0644
            zip.writestr(info, filecontent)
        zip.close()
        self.write({'file': base64.encodestring(s.getvalue()), 'state': 'done'})

    @api.multi
    def set_to_draft(self):
        return self.write({'state': 'draft', 'file': False})

    @api.multi
    def open_wizard(self):
        self.ensure_one()
        return {
            'name': _('Export Customizations as a Module'),
            'view_type': 'form',
            'view_mode': 'form',
            'view_id': False,
            'res_model': 'base.module.record',
            'domain': [],
            'context': self._context,
            'type': 'ir.actions.act_window',
            'target': 'new',
            'res_id': self.id,
        }

    @api.multi
    def button_create_module(self):
        self.create_module()
        return self.open_wizard()

    @api.multi
    def button_set_to_draft(self):
        self.set_to_draft()
        return self.open_wizard()
