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
import calendar
import datetime
from ftplib import FTP
import logging
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

def _render_unicode(template_src, localdict, encoding='UTF-8'):
    template = MakoTemplate(tools.ustr(template_src), output_encoding=encoding)
    return template.render_unicode(**localdict)

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
        'filename': fields.char('Filename', size=256, required=True, help="You can use a mako language "
            "with the object and time variables"),
        'encoding': fields.selection([
            ('UTF-8', 'UTF-8'),
            ('ISO-8859-15', 'ISO-8859-15'),
        ], 'Encoding', required=True),
        'exception_handling': fields.selection([
            ('cancel', 'Cancel export'),
            ('continue', 'Ignore wrong line'),
        ], 'Exception Handling', required=True),
        'exception_logging': fields.selection([
            ('report', 'Included in report'),
            ('file', 'Dedicated file'),
        ], 'Exception Logging', required=True),
        'delimiter': fields.char('Delimiter', size=64),
        'lineterminator': fields.char('Line Terminator', size=64),
        'fieldnames_in_header': fields.boolean('Fieldnames in header'),
        'column_ids': fields.one2many('ir.model.export.file_template.column', 'export_file_template_id', 'Columns'),
        'header': fields.text('Header'),
        'body': fields.text('Body', help="Template language: Mako"),
        'footer': fields.text('Footer'),
        'report_summary_template': fields.text('Report', help="Use mako language with the pool, cr, uid, object, "
            "context, time, datetime, start_date, end_date, filename, records_number, exceptions_number and exceptions variables"),
        'create_attachment': fields.boolean('Create an attachement'),
        'upload_to_ftp_server': fields.boolean('Upload to FTP server'),
        'ftp_host': fields.char('Host', size=128),
        'ftp_anonymous': fields.boolean('Anonymous'),
        'ftp_user': fields.char('User', size=64),
        'ftp_password': fields.char('Password', size=64),
    }

    _defaults = {
        'exception_handling': lambda * a: 'cancel',
        'exception_logging': lambda * a: 'report',
        'delimiter': lambda * a: "','",
        'lineterminator': lambda * a: "'\n'",
        'create_attachment': lambda * a: True,
        'report_summary_template': lambda * a: """Here is the file export processing report.

        File export: ${object.id}
        Start Time: ${start_time}
        End Time: ${end_time}
        File name: ${filename}
        Resources exported: ${records_number - exceptions_number}
        Resources in exception: ${exceptions_number}
""",
    }

    # ***** Data layout methods ****

    def _render_xml(self, cr, uid, export_file, template_part, localdict):
        """Render the output of this template as a string formated in XML"""
        return _render_unicode(getattr(export_file, template_part), localdict, export_file.encoding)

    def _render_csv(self, cr, uid, export_file, template_part, localdict):
        """Render the output of this template as a string formated in CSV"""
        template = []
        try:
            delimiter = eval(export_file.delimiter)
        except:
            delimiter = export_file.delimiter
        # Header & Footer
        if getattr(export_file, template_part):
            template.append(self._render_xml(cr, uid, export_file, template_part, localdict))
        # Header with fieldnames
        if template_part == 'header' and export_file.fieldnames_in_header:
            template.append(delimiter.join([tools.ustr(column.name) for column in export_file.column_ids]))
        # Body
        if template_part == 'body':
            line = []
            for column in export_file.column_ids:
                column_value = _render_unicode(column.value, localdict)
                if column.default_value and not column_value:
                    column_value = _render_unicode(column.default_value, localdict)
                if column.not_none and column_value is None:
                    try:
                        exception_msg = _render_unicode(column.exception_msg, localdict)
                    except:
                        exception_msg = column.exception_msg
                    raise osv.except_osv(_('Error'), exception_msg)
                column_value = tools.ustr(column_value)
                if column_value:
                    if column.min_width:
                        column_value = getattr(column_value, column.justify)(column.min_width, tools.ustr(column.fillchar))
                    if column.max_width:
                        column_value = column_value[:column.max_width]
                line.append(column_value)
            template.append(delimiter.join(line))
        try:
            lineterminator = eval(export_file.lineterminator)
        except:
            lineterminator = export_file.lineterminator
        return lineterminator.join(template)

    def _lay_out_data(self, cr, uid, export_file, context):
        """Call specific layout methods and catch exceptions"""
        content = []
        exceptions = []
        content_render_method = export_file.state in ['csv', 'xml'] and '_render_' + export_file.state or export_file.layout_method
        if content_render_method:
            localdict = {
                'pool': self.pool,
                'cr': cr,
                'uid': uid,
                'context': context,
                'time': time,
                'datetime': datetime,
                'calendar': calendar,
            }
            objects = self.pool.get(export_file.model_id.model).browse(cr, uid, context['active_ids'], context)
            for template_part in ['header', 'body', 'footer']:
                if export_file.state == 'csv' and export_file.column_ids or getattr(export_file, template_part):
                    template_parts = template_part == 'body' and objects or [objects]
                    for line in template_parts:
                        localdict['object'] = line
                        try:
                            content.append(getattr(self, content_render_method)(cr, uid, export_file, template_part, localdict))
                        except Exception, e:
                            if template_part == 'body' and export_file.exception_handling == 'continue':
                                exceptions.append('%s,%s: %s' % (export_file.model, line.id, _get_exception_message(e)))
                            else:
                                raise
        try:
            lineterminator = eval(export_file.lineterminator)
        except:
            lineterminator = export_file.lineterminator
        return (lineterminator.join(content), exceptions)

    # ***** File saving methods *****

    def _create_attachement(self, cr, uid, export_file, filename, binary, context):
        vals = {
            'name': filename,
            'type': 'binary',
            'datas': binary,
            'datas_fname': filename,
            'res_model': 'ir.model.export',
            'res_id': context.get('attach_export_id', 0),
        }
        self.pool.get('ir.attachment').create(cr, uid, vals, context)

    def _upload_to_ftp_server(self, cr, uid, export_file, filename, binary, context):
        ftp = FTP(export_file.ftp_host)
        if export_file.ftp_anonymous:
            ftp.login()
        else:
            ftp.login(export_file.ftp_user, export_file.ftp_password or '')
        command = 'STOR %s' % filename
        file = open(filename, 'w')
        file.write(binary)
        ftp.storbinary(command, file)

    def _save_file(self, cr, uid, export_file, filename, binary, context):
        for save_file_method in ['create_attachment', 'upload_to_ftp_server']:
            if getattr(export_file, save_file_method):
                getattr(self, '_' + save_file_method)(cr, uid, export_file, filename, binary, context)

    # ***** Execution report saving method *****

    def _save_execution_report(self, cr, uid, export_file, localdict):
        filename = localdict['filename']
        exceptions = localdict['exceptions']
        context = localdict['context']
        summary = _render_unicode(export_file.report_summary_template, localdict)
        if exceptions and export_file.exception_logging == 'report':
            summary += "Exceptions:\n%s" % '\n'.join(exceptions)
        report_vals = {
            'name': "File Export Processing Report",
            'act_from': uid,
            'act_to': uid,
            'body': summary,
        }
        report_id = self.pool.get('res.request').create(cr, uid, report_vals, context)
        if exceptions and export_file.exception_logging == 'report':
            exceptions_filename = filename[:-filename.find('.')] + '.ERRORS' + filename[-filename.find('.'):]
            exceptions_vals = {
                'name':  exceptions_filename,
                'type': 'binary',
                'datas': base64.encodestring('\n'.join(exceptions).encode(export_file.encoding)),
                'datas_fname': exceptions_filename,
                'res_model': 'res.request',
                'res_id': report_id,
            }
            self.pool.get('ir.attachment').create(cr, uid, exceptions_vals, context)
        export = self.pool.get('ir.model.export').browse(cr, uid, context.get('attach_export_id', 0), context)
        return export.write({'report_id': report_id})

    # ***** File generation method *****

    def generate_file(self, cr, uid, export_file_id, context=None):
        """Check and lay out data, save file and produce an export processing report"""
        start_date = time.strftime('%Y-%m-%d %H:%M:%S')

        context = context or {}
        if isinstance(export_file_id, list):
            export_file_id = export_file_id[0]
        export_file = self.browse(cr, uid, export_file_id, context)
        filename = ''
        exceptions = []
        content_ids = context.get('active_ids', 'active_id' in context and [context['active_id']] or [])
        checked_content_ids = content_ids[:]
        if export_file.check_method:
            checked_content_ids = []
            content_model = self.pool.get(export_file.model)
            for content_id in content_ids:
                try:
                    if getattr(content_model, export_file.check_method)(cr, uid, content_id, context):
                        checked_content_ids.append(content_id)
                    else:
                        exceptions.append('%s,%s: %s' % (export_file.model, content_id, 'Check failed'))
                except Exception, e:
                    exceptions.append('%s,%s: %s' % (export_file.model, content_id, _get_exception_message(e)))
        if checked_content_ids:
            context['active_ids'] = checked_content_ids
            file_content, content_exceptions = self._lay_out_data(cr, uid, export_file, context)
            exceptions += content_exceptions
            if file_content:
                filename = _render_unicode(export_file.filename, {'object': export_file, 'context': context, 'time': time}, export_file.encoding)
                binary = base64.encodestring(file_content.encode(export_file.encoding))
                self._save_file(cr, uid, export_file, filename, binary, context)
        end_date = time.strftime('%Y-%m-%d %H:%M:%S')
        localdict = {
            'pool': self.pool,
            'cr': cr,
            'uid': uid,
            'object': export_file,
            'context': context,
            'time': time,
            'datetime': datetime,
            'calendar': calendar,
            'start_date': start_date,
            'end_date': end_date,
            'filename': filename,
            'file': binary,
            'records_number': len(content_ids),
            'exceptions_number': len(exceptions),
            'exceptions': exceptions}
        return self._save_execution_report(cr, uid, export_file, localdict)
ir_model_export_file_template()

class ir_model_export_file_template_column(osv.osv):
    _name = 'ir.model.export.file_template.column'
    _description = 'Export File Template Column'

    _columns = {
        'name': fields.char('Label', size=64, required=True),
        'sequence': fields.integer('Sequence', required=True),
        'export_file_template_id': fields.many2one('ir.model.export.file_template', 'Export', required=True, ondelete='cascade'),
        'value': fields.text('Value', required=True,
            help="Use mako language with the pool, cr, uid, object, context and time variables"),
        'default_value': fields.char('Default value', size=64,
            help="Use mako language with the pool, cr, uid, object, context and time variables"),
        'not_none': fields.boolean('Not None?'),
        'exception_msg': fields.char('Exception Message', size=256, translate=True,
            help="Use mako language with the pool, cr, uid, object, context and time variables"),
        'min_width': fields.integer('Min width'),
        'fillchar': fields.char('Fillchar', size=1),
        'justify': fields.selection([
            ('ljust', 'Left'),
            ('rjust', 'Right'),
        ], 'Justify'),
        'max_width': fields.integer('Max width'),
    }
ir_model_export_file_template_column()
