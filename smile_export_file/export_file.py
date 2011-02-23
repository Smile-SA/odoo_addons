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

import base64
import logging
import StringIO
import time

try:
    from mako.template import Template as MakoTemplate
except ImportError:
    logging.getLogger("import").exception("Mako package is not installed")

from osv import osv, fields
import tools
from tools.translate import _

def _get_exception_message(exception):
    return isinstance(exception, osv.except_osv) and exception.value or exception

class ir_model_export_file_template(osv.osv):
    _name = 'ir.model.export.file_template'
    _description = 'Export File Template'

    _columns = {
        'name': fields.char('Name', size=64, required=True),
        'model_id': fields.many2one('ir.model', 'Object', domain=[('osv_memory', '=', False)], required=True, ondelete='cascade'),
        'model': fields.related('model_id', 'model', type='char', string='Object', readonly=True),
        'state': fields.selection([
            ('xml', 'XML'),
            ('csv', 'CSV'),
            ('custom', 'Custom'),
        ], 'Type', required=True),
        'layout_method': fields.char('Data Layout Method', size=64, help="Indicate a method of the object "
            "'ir.model.export_file' with a signature equals to (self, cr, uid, export_file_instance, template_part, localdict)"),
        'check_method': fields.char('Data Check Method', size=64, help="Indicate a method of the "
            "remote model with a signature equals to (self, cr, uid, ids, context=None)"),
        'filename': fields.char('Filename', size=256, required=True, help="You can use a python expession "
            "with the object and time variables"),
        'encoding': fields.selection([
            ('UTF-8', 'UTF-8'),
            ('ISO-8859-15', 'ISO-8859-15'),
        ], 'Encoding', required=True),
        'exception_handling': fields.selection([
            ('cancel', 'Cancel export'),
            ('continue', 'Ignore wrong line'),
        ], 'Exception Handling', required=True),
        'report_id': fields.many2one('res.request', 'Report', readonly=True),
        'delimiter': fields.char('Delimiter', size=64),
        'lineterminator': fields.char('Line Terminator', size=64),
        'fieldnames_in_header': fields.boolean('Fieldnames in header'),
        'column_ids': fields.one2many('ir.model.export.file_template.column', 'export_file_template_id', 'Columns'),
        'header': fields.text('Header'),
        'body': fields.text('Body', help="Template language: Mako"),
        'footer': fields.text('Footer'),
        'create_attachment': fields.boolean('Create an attachement'),
    }

    _defaults = {
        'exception_handling': lambda * a: 'cancel',
        'delimiter': lambda * a: "','",
        'lineterminator': lambda * a: "chr(10)",
        'create_attachment': lambda * a: True,
    }

    def _render_xml(self, cr, uid, export_file, template_part, localdict):
        """Render the output of this template as a string formated in XML"""
        template_src = getattr(export_file, template_part)
        template = MakoTemplate(tools.ustr(template_src), output_encoding=export_file.encoding)
        return template.render_unicode(**localdict)

    def _render_csv(self, cr, uid, export_file, template_part, localdict):
        """Render the output of this template as a string formated in CSV"""
        template = []
        # Header & Footer
        if getattr(export_file, template_part):
            template_src = tools.ustr(getattr(export_file, template_part))
            template.append(eval(template_src, localdict))
        # Header with fieldnames
        if template_part == 'header' and export_file.fieldnames_in_header:
            template.append(export_file.delimiter.join([tools.ustr(column.name) for column in export_file.column_ids]))
        # Body
        if template_part == 'body':
            line = []
            for column in export_file.column_ids:
                column_value = tools.ustr(column.value)
                if column.default_value and not column_value:
                    column_value = tools.ustr(column.default_value)
                if column_value:
                    if column.min_width:
                        column_value = getattr(column_value, column.justify)(column.min_width, tools.ustr(column.fillchar))
                    if column.max_width:
                        column_value = column_value[:column.max_width]
                    column_value = eval(column_value, localdict)
                if column.not_none and not column_value:
                    raise osv.except_osv(_('Error'), column.exception_msg)
                line.append(column_value)
            template.append(export_file.delimiter.join(line))
        return export_file.lineterminator.join(template)

    def _lay_out_data(self, cr, uid, export_file, context):
        """Call specific layout methods and catch exceptions"""
        content = report = []
        content_render_method = export_file.state in ['csv', 'xml'] and '_render_' + export_file.state or export_file.layout_method
        if content_render_method:
            localdict = {
                'pool': self.pool,
                'cr': cr,
                'uid': uid,
                'context': context,
                'time': time,
            }
            objects = self.pool.get(export_file.model_id.model).browse(cr, uid, context['active_ids'], context)
            for template_part in ['header', 'body', 'footer']:
                if getattr(export_file, template_part):
                    template_parts = template_part == 'body' and objects or [objects]
                    for line in template_parts:
                        localdict['object'] = line
                        try:
                            content.append(getattr(self, content_render_method)(cr, uid, export_file, template_part, localdict))
                        except Exception, e:
                            if template_part == 'body' and export_file.exception_handling == 'continue':
                                report.append('%s,%s: %s' % (export_file.model, line.id, _get_exception_message(e)))
                            else:
                                raise
        return (export_file.lineterminator.join(content), report)

    def _save_file(self, cr, uid, export_file, filename, buffer_file, context):
        if export_file.create_attachment:
            vals = {
                'name': filename,
                'datas': base64.encodestring(buffer_file.getvalue().encode(export_file.encoding)),
                'datas_fname': filename,
                'res_model': context.get('attach_res_model', self._name),
                'res_id': context.get('attach_res_id', export_file.id),
            }
            self.pool.get('ir.attachment').create(cr, uid, vals, context)

    def generate_file(self, cr, uid, export_file_id, context=None):
        """Check and lay out data, save file and produce an export processing report"""
        start_date = time.strftime('%Y-%m-%d %H:%M:%S')

        context = context or {}
        if isinstance(export_file_id, list):
            export_file_id = export_file_id[0]
        export_file = self.browse(cr, uid, export_file_id, context)
        filename = ''
        report = []
        content_ids = checked_content_ids = context.get('active_ids', 'active_id' in context and [context['active_id']] or [])
        if export_file.check_method:
            checked_content_ids = []
            content_model = self.pool.get(export_file.model)
            for content_id in content_ids:
                if getattr(content_model, export_file.check_method)(cr, uid, content_id, context):
                    checked_content_ids.append(content_id)
                else:
                    report.append('%s,%s: %s' % (export_file.model, content_id, 'Check failed'))
        if checked_content_ids:
            context['active_ids'] = checked_content_ids
            file_content, report2 = self._lay_out_data(cr, uid, export_file, context)
            report += report2
            if file_content:
                buffer_file = StringIO.StringIO()
                buffer_file.write(file_content)
                try:
                    filename = eval(export_file.filename, {'object': export_file, 'time': time})
                except:
                    filename = export_file.filename
                self._save_file(cr, uid, export_file, filename, buffer_file, context)

        end_date = time.strftime('%Y-%m-%d %H:%M:%S')
        summary = """Here is the file export processing report.

        File export: %d
        Start Time: %s
        End Time: %s
        File name: %s
        Resources exported: %d
        Resources in exception: %d

        Exceptions:\n%s""" % (export_file.id, start_date, end_date, filename, len(content_ids) - len(report), len(report), '\n'.join(report))
        vals = {
            'name': "File Export Processing Report",
            'act_from': uid,
            'act_to': uid,
            'body': summary,
        }
        report_id = self.pool.get('res.request').create(cr, uid, vals, context)
        return export_file.write({'report_id': report_id})
ir_model_export_file_template()

class ir_model_export_file_template_column(osv.osv):
    _name = 'ir.model.export.file_template.column'
    _description = 'Export File Template Column'

    _columns = {
        'name': fields.char('Label', size=64, required=True),
        'sequence': fields.integer('Sequence', required=True),
        'export_file_template_id': fields.many2one('ir.model.export.file_template', 'Export', required=True, ondelete='cascade'),
        'value': fields.text('Value', required=True, help="Use a python expression with the pool, cr, uid, object, "
            "context and time variables"),
        'default_value': fields.char('Default value', size=64, help="Use a python expression with the pool, cr, uid, "
            "object, context and time variables"),
        'not_none': fields.boolean('Not None?'),
        'exception_msg': fields.char('Exception Message', size=256, translate=True),
        'min_width': fields.integer('Min width'),
        'fillchar': fields.char('Fillchar', size=1),
        'justify': fields.selection([
            ('ljust', 'Left'),
            ('rjust', 'Right'),
        ], 'Justify'),
        'max_width': fields.integer('Max width'),
    }
ir_model_export_file_template_column()
