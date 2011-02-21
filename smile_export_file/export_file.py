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

class ir_model_export_file(osv.osv):
    _name = 'ir.model.export_file'
    _description = 'Export File'

    _columns = {
        'name': fields.char('Name', size=64, required=True),
        'model_id': fields.many2one('ir.model', 'Object', domain=[('osv_memory', '=', False)], required=True, ondelete='cascade'),
        'state': fields.selection([
            ('xml', 'XML'),
            ('csv', 'CSV'),
            ('custom', 'Custom'),
        ], 'Type', required=True),
        'render_method': fields.char('Content Render Method', size=64, help="Indicate a method of the object "
            "'ir.model.export_file' with a signature equals to (self, cr, uid, export_file_instance, template_part, localdict, context=None)"),
        'check_method': fields.char('Content Check Method', size=64, help="Indicate a method of the "
            "remote model with a signature equals to (self, cr, uid, ids, context=None)"),
        'filename': fields.char('Filename', size=256, required=True, help="You can use a python expession "
            "with the object and time variables"),
        'encoding': fields.selection([
            ('UTF-8', 'UTF-8'),
            ('ISO-8859-15', 'ISO-8859-15'),
        ], 'Encoding', required=True),
        'log_level': fields.selection([
            ('ERROR', 'ERROR'),
            ('INFO', 'INFO'),
        ], 'Log level', required=True),
        'exception_handling': fields.selection([
            ('cancel', 'Cancel export'),
            ('continue', 'Ignore wrong line'),
        ], 'Exception Handling', required=True),
        'delimiter': fields.char('Delimiter', size=64),
        'lineterminator': fields.char('Line Terminator', size=64),
        'fieldnames_in_header': fields.boolean('Fieldnames in header'),
        'column_ids': fields.one2many('ir.model.export_file.column', 'export_file_id', 'Columns'),
        'header': fields.text('Header'),
        'body': fields.text('Body', help="Template language: Mako"),
        'footer': fields.text('Footer'),
    }

    _defaults = {
        'log_level': lambda * a: 'ERROR',
        'exception_handling': lambda * a: 'cancel',
        'delimiter': lambda * a: "','",
        'lineterminator': lambda * a: "'\n'",
    }

    def _build_localdict(self, cr, uid, export_file, context=None):
        context = context or {}
        ids = context.get('active_ids', 'active_id' in context and [context['active_id']] or [])
        return {
            'pool': self.pool,
            'cr': cr,
            'uid': uid,
            'object': self.pool.get(export_file.model_id.model).browse(cr, uid, ids, context),
            'context': context,
            'time': time,
        }

    def _render_xml(self, cr, uid, export_file, template_part, localdict, context=None):
        template_src = getattr(export_file, template_part)
        template = MakoTemplate(tools.ustr(template_src), output_encoding=export_file.encoding)
        return template.render_unicode(**localdict)

    def _render_csv(self, cr, uid, export_file, template_part, localdict, context=None):
        template = ''
        # Header & Footer
        if getattr(export_file, template_part):
            template_src = tools.ustr(getattr(export_file, template_part))
            template += eval(template_src, localdict)
        # Header with fieldnames
        if template_part == 'header' and export_file.fieldnames_in_header:
            template += export_file.lineterminator
            template += export_file.delimiter.join([tools.ustr(column.name) for column in export_file.column_ids])
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
            template += export_file.delimiter.join(line)
        return template

    def _log_exception(self, cr, uid, vals, context=None):
        if isinstance(vals['name'], osv.except_osv):
            vals['name'] = vals['name'].value
        return self.pool.get('ir.model.export_file.log').create(cr, uid, vals, context)

    def _render_content(self, cr, uid, export_file, context=None):
        content = []
        content_render_method = export_file.state in ['csv', 'xml'] and '_render_' + export_file.state or export_file.render_method
        localdict = self._build_localdict(cr, uid, export_file, context)
        # Header
        if export_file.header:
            try:
                content.append(getattr(self, content_render_method)(cr, uid, export_file, 'header', localdict, context))
            except Exception, e:
                self._log_exception(cr, uid, {'name': e, 'export_file_id': export_file.id}, context)
                return ''
        # Body
        if export_file.body:
            localdict_copy = localdict.copy()
            for line in localdict['object']:
                localdict_copy['object'] = line
                try:
                    content.append(getattr(self, content_render_method)(cr, uid, export_file, 'body', localdict_copy, context))
                except:
                    self._log_exception(cr, uid, {'name': e, 'export_file_id': export_file.id, 'res_id': line.id}, context)
                    if export_file.exception_handling == 'continue':
                        continue
                    else:
                        return ''
        # Footer
        if export_file.footer:
            try:
                content.append(getattr(self, content_render_method)(cr, uid, export_file, 'footer', localdict, context))
            except Exception, e:
                self._log_exception(cr, uid, {'name': e, 'export_file_id': export_file.id}, context)
                return ''
        return export_file.lineterminator.join(content)

    def generate_file(self, cr, uid, ids, context=None):
        if isinstance(ids, (int, long)):
            ids = [ids]
        context = context or {}
        for export_file in self.browse(cr, uid, ids, context):
            check_content_ok = True
            if export_file.check_method:
                content_ids = context.get('active_ids', 'active_id' in context and [context['active_id']] or [])
                content_model = self.pool.get(export_file.model_id.model)
                check_content_ok = getattr(content_model, export_file.check_method)(cr, uid, content_ids, context)
            if check_content_ok:
                file_content = self._render_content(cr, uid, export_file, context)
                buffer_file = StringIO.StringIO()
                buffer_file.write(file_content)
                try:
                    filename = eval(export_file.filename, {'object': export_file, 'time': time})
                except Exception, e:
                    self._log_exception(cr, uid, {'name': e, 'export_file_id': export_file.id}, context)
                    filename = export_file.filename
                vals = {
                    'name': filename,
                    'datas': base64.encodestring(buffer_file.getvalue().encode(export_file.encoding)),
                    'datas_fname': filename,
                    'res_model': self._name,
                    'res_id': export_file.id,
                }
                self.pool.get('ir.attachment').create(cr, uid, vals, context=context)
        return True
ir_model_export_file()

class ir_model_export_file_column(osv.osv):
    _name = 'ir.model.export_file.column'
    _description = 'Export File Column'

    _columns = {
        'name': fields.char('Label', size=64, required=True),
        'export_file_id': fields.many2one('ir.model.export_file', 'Export', required=True, ondelete='cascade'),
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
ir_model_export_file_column()

class ir_model_export_file_log(osv.osv):
    _name = 'ir.model.export_file.log'
    _description = 'Export File Logs'

    _columns = {
        'name': fields.char('Message', size=256, help='The logging message.', required=True),
        'create_date': fields.datetime('Creation Date', readonly=True),
        'export_file_id': fields.many2one('ir.model.export_file', 'Export File', required=True),
        'res_id': fields.integer('Resource ID'),
    }
ir_model_export_file_log()
