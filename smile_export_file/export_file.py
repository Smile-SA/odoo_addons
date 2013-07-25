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
import os.path
import logging
import pytz
from random import random
import tempfile
from tempfile import mkstemp
import time
import unicodedata

try:
    from mako.template import Template as MakoTemplate
except ImportError:
    logging.getLogger("import").exception("Mako package is not installed")

from osv import osv, fields
import tools
from tools.translate import _

from text2pdf import pyText2Pdf


def strip_accents(s):
    u = isinstance(s, unicode) and s or unicode(s, 'utf8')
    a = ''.join((c for c in unicodedata.normalize('NFKD', u) if unicodedata.category(c) != 'Mn'))
    return str(a)


def is_a_datetime(str0, type_='datetime'):
    if isinstance(str0, basestring):
        formats = {
            'datetime': '%Y-%m-%d %H:%M:%S',
            'date': '%Y-%m-%d',
            'time': '%Y-%m-%d %H:%M:%S',
        }
        try:
            if type_ == 'time':
                str0 = datetime.datetime.today().strftime(formats['date']) + ' ' + str0
            result = datetime.datetime.strptime(str0, formats[type_])
            return result
        except Exception:
            pass
    return


def format_lang(pool, cr, value, lang='en_US', digits=2, tz='America/New_York'):
    lang_obj = pool.get('res.lang')
    lang_id = lang_obj.search(cr, 1, [('code', '=', lang)], limit=1)
    if lang_id:
        lang = lang_obj.read(cr, 1, lang_id[0], ['date_format', 'time_format'])
        output_formats = {
            'datetime': '%s %s' % (lang['date_format'], lang['time_format']),
            'date': str(lang['date_format']),
            'time': str(lang['time_format']),
        }
        for type in output_formats:
            if is_a_datetime(value, type):
                if tz:
                    return pytz.timezone(tz).fromutc(is_a_datetime(value)).strftime(output_formats[type])
                else:
                    return is_a_datetime(value).strftime(output_formats[type])
        return lang_obj.format(cr, 1, lang_id, '%.' + str(digits) + 'f', value)
    return value


def _get_exception_message(exception):
    return isinstance(exception, osv.except_osv) and exception.value or exception


def _render_unicode(template_src, localdict, encoding='UTF-8'):
    template = MakoTemplate(tools.ustr(template_src), output_encoding=encoding)
    return template.render_unicode(**localdict)


def _text2pdf(string):
    tmpfilename = os.path.join(tempfile.gettempdir(), str(int(random() * 10 ** 9)))
    tmpfile = open(tmpfilename, 'w')
    tmpfile.write(string)
    tmpfile.close()
    pdf = pyText2Pdf()
    pdf._ifile = tmpfilename
    pdf.Convert()
    tmpfile_pdf = open(tmpfilename + '.pdf', 'r')
    string = tmpfile_pdf.read()
    os.remove(tmpfilename)
    os.remove(tmpfilename + '.pdf')
    return string


class ir_model_export_file_template(osv.osv):
    _name = 'ir.model.export.file_template'
    _description = 'Export File Template'

    _columns = {
        'name': fields.char('Name', size=64, required=True),
        'model_id': fields.many2one('ir.model', 'Object', domain=[('osv_memory', '=', False)], required=True, ondelete='cascade'),
        'model': fields.related('model_id', 'model', type='char', string='Object', readonly=True),
        'refer_to_underlying_object': fields.boolean('Columns correspond to an underlying object'),
        'records': fields.char('Records', size=256, help="Provide the field name that refers to the records to export. "
                                                         "If it is empty it will refer to the current object."),
        'state': fields.selection([
            ('tab', 'Tabular'),
            ('other', 'Other'),
        ], 'Type', required=True),
        'check_method': fields.char('Data Check Method', size=64, help="Indicate a method of the "
                                    "remote model with a signature equals to (self, cr, uid, ids, context=None)"),
        'filename': fields.char('Filename', size=256, required=True, help="You can use a mako language "
                                "with the object and time variables"),
        'extension': fields.selection([
            ('pdf', '.pdf'),
            ('other', 'other'),
        ], 'Extension', required=True),
        'extension_custom': fields.char('Custom Extension', size=12),
        'encoding': fields.selection([
            ('UTF-8', 'UTF-8'),
            ('ISO-8859-15', 'ISO-8859-15'),
            ('cp1252', 'Windows-CP1252'),
        ], 'Encoding', required=True),
        'exception_handling': fields.selection([
            ('cancel', 'Cancel export'),
            ('continue', 'Ignore wrong line'),
        ], 'Exception Handling', required=True),
        'exception_logging': fields.selection([
            ('report', 'Included in report'),
            ('file', 'Dedicated file'),
        ], 'Exception Logging', required=True),
        'delimiter': fields.char('Delimiter', size=24),
        'lineterminator': fields.char('Line Terminator', size=24),
        'quotechar': fields.char('Quote Character', size=24),
        'fieldnames_in_header': fields.boolean('Add column labels in header'),
        'column_ids': fields.one2many('ir.model.export.file_template.column', 'export_file_template_id', 'Columns'),
        'header': fields.text('Header'),
        'body': fields.text('Body', help="Template language: Mako"),
        'footer': fields.text('Footer'),

        'report_summary_template': fields.text('Report', help="Use mako language with the pool, cr, uid, object, "
                                               "context, time, datetime, start_date, end_date, filename, records_number, "
                                               "exceptions_number and exceptions variables"),

        'create_attachment': fields.boolean('Create an attachement'),
        'upload_to_ftp_server': fields.boolean('Upload to FTP server'),
        'ftp_host': fields.char('Host', size=128, help="You can use a mako language "
                                "with the object and time variables"),
        'ftp_anonymous': fields.boolean('Anonymous'),
        'ftp_user': fields.char('User', size=64),
        'ftp_password': fields.char('Password', size=64),
        'ftp_directory': fields.char('Directory', size=128),
        'save_in_local_dir': fields.boolean('Save in a local directory'),
        'local_directory': fields.char('Local directory', size=128),
        'send_by_email': fields.boolean('Send by email'),
        'email_to': fields.char('To', size=128),
        'email_cc': fields.char('CC', size=128),
        'email_subject': fields.char('Subject', size=256),
        'email_body': fields.text('Body'),
        'email_attach_export_file': fields.boolean('Attach export file'),
        'email_attach_exceptions_file': fields.boolean('Attach exceptions file'),
    }

    _defaults = {
        'state': lambda * a: 'other',
        'extension': lambda * a: 'other',
        'exception_handling': lambda * a: 'cancel',
        'exception_logging': lambda * a: 'report',
        'delimiter': lambda * a: "chr(44)",
        'lineterminator': lambda * a: "chr(10)",
        'quotechar': lambda * a: "chr(34)",
        'create_attachment': lambda * a: True,
        'report_summary_template': lambda * a: """Here is the file export processing report.

        File export: ${object.id}
        Start Time: ${start_time}
        End Time: ${end_time}
        File name: ${filename}
        Resources exported: ${records_number - exceptions_number}
        Resources in exception: ${exceptions_number}
""",
        'email_attach_export_file': lambda * a: True,
    }

    # ***** Data layout methods ****

    def _render(self, cr, uid, export_file, template_part, localdict):
        """Render the output of this template as a string"""
        return _render_unicode(getattr(export_file, template_part), localdict, export_file.encoding)

    def _render_tab(self, cr, uid, export_file, template_part, localdict):
        """Render the output of this template in a tabular format"""
        template = []
        try:
            delimiter = eval(export_file.delimiter)
        except TypeError:
            delimiter = export_file.delimiter
        # Header & Footer
        if getattr(export_file, template_part):
            template.append(self._render(cr, uid, export_file, template_part, localdict))
        # Header with fieldnames
        if template_part == 'header' and export_file.fieldnames_in_header:
            template.append(delimiter.join([tools.ustr(column.name) for column in export_file.column_ids]))
        # Body
        if template_part == 'body':
            sub_objects = localdict['object']
            if export_file.refer_to_underlying_object:
                sub_objects = eval(export_file.records, localdict)
            if not isinstance(sub_objects, list):
                sub_objects = [sub_objects]
            for index, sub_object in enumerate(sub_objects):
                localdict['line_number'] = index + 1
                localdict['object'] = sub_object
                line = []
                for column in export_file.column_ids:
                    try:
                        column_value = _render_unicode(column.value or '', localdict)
                        if column.default_value and not column_value:
                            column_value = _render_unicode(column.default_value, localdict)
                        if column.column_validator:
                            validation = eval(column.column_validator, localdict)
                            if not validation:
                                try:
                                    exception_msg = _render_unicode(column.exception_msg, localdict)
                                except Exception:
                                    exception_msg = column.exception_msg
                                raise osv.except_osv(_('Error'), exception_msg)
                        column_value = tools.ustr(column_value)
                        if column_value:
                            if column.min_width:
                                column_value = getattr(column_value, column.justify)(column.min_width, tools.ustr(column.fillchar))
                            if column.max_width:
                                column_value = column_value[: column.max_width]
                        if not column.not_string and export_file.quotechar:
                            try:
                                quotechar = export_file.quotechar and eval(export_file.quotechar) or ''
                            except TypeError:
                                quotechar = export_file.quotechar
                            column_value = '%(quotechar)s%(column_value)s%(quotechar)s' % {
                                'column_value': quotechar and column_value.replace(quotechar, "\\" + quotechar) or column_value,
                                'quotechar': quotechar,
                            }
                        line.append(column_value)
                    except Exception, e:
                        raise osv.except_osv(_('Error'), 'column %s: %s' % (column.name, e))
                template.append(delimiter.join(line))
        try:
            lineterminator = eval(export_file.lineterminator)
        except TypeError:
            lineterminator = export_file.lineterminator
        return lineterminator.join(template)

    def _lay_out_data(self, cr, uid, export_file, context):
        """Call specific layout methods and catch exceptions"""
        content = []
        exceptions = []
        content_render_method = export_file.state == 'tab' and '_render_tab' or '_render'
        if content_render_method and context['active_ids']:
            localdict = {
                'pool': self.pool,
                'cr': cr,
                'uid': uid,
                'localcontext': context,
                'time': time,
                'datetime': datetime,
                'calendar': calendar,
                'format_lang': format_lang,
                'strip_accents': strip_accents,
            }
            objects = self.pool.get(export_file.model_id.model).browse(cr, uid, context['active_ids'], context)
            for template_part in ['header', 'body', 'footer']:
                if export_file.state == 'tab' and export_file.column_ids or getattr(export_file, template_part):
                    template_parts = template_part == 'body' and objects or [objects]
                    for line in template_parts:
                        localdict['object'] = line
                        try:
                            content.append(getattr(self, content_render_method)(cr, uid, export_file, template_part, localdict))
                        except Exception, e:
                            if template_part == 'body' and export_file.exception_handling == 'continue':
                                exceptions.append('%s - %s, %s: %s' % (template_part, export_file.model, line.id, _get_exception_message(e)))
                            else:
                                raise Exception('%s - %s' % (template_part, _get_exception_message(e)))
        try:
            lineterminator = eval(export_file.lineterminator)
        except TypeError:
            lineterminator = export_file.lineterminator
        return (lineterminator.join(content), exceptions)

    # ***** File storage methods *****

    def _create_attachment(self, cr, uid, export_file, filename, file_content, context):
        vals = {
            'name': filename,
            'type': 'binary',
            'datas': file_content and base64.encodestring(file_content) or ' ',
            'datas_fname': filename,
            'res_model': 'ir.model.export',
            'res_id': context.get('attach_export_id', 0),
        }
        self.pool.get('ir.attachment').create(cr, uid, vals, context)

    def _save_in_local_dir(self, cr, uid, export_file, filename, file_content, context):
        directory = os.path.abspath(export_file.local_directory)
        if not os.path.exists(directory):
            raise Exception('Directory %s does not exist or permission on it is not granted' % (directory, ))
        file = open(directory + '/' + filename, 'w')
        file.write(file_content)
        file.close()

    def _upload_to_ftp_server(self, cr, uid, export_file, filename, file_content, context):
        localdict = {
            'object': export_file,
            'localcontext': context,
            'time': time,
        }
        host = _render_unicode(export_file.ftp_host, localdict)
        ftp = FTP(host)
        if export_file.ftp_anonymous:
            ftp.login()
        else:
            ftp.login(export_file.ftp_user, export_file.ftp_password or '')
        if export_file.ftp_directory:
            ftp.cwd(export_file.ftp_directory)
        fd, temp_path = mkstemp()
        file = open(temp_path, 'wb')
        file.write(file_content)
        file.close()
        os.close(fd)
        file = open(temp_path, 'rb')
        ftp.storbinary('STOR %s' % filename, file)
        file.close()
        os.remove(temp_path)

    def _save_file(self, cr, uid, export_file, filename, file_content, context):
        for save_file_method in ['create_attachment', 'upload_to_ftp_server', 'save_in_local_dir']:
            if getattr(export_file, save_file_method):
                try:
                    getattr(self, '_' + save_file_method)(cr, uid, export_file, filename, file_content, context)
                except osv.except_osv, e:
                    exception_infos = "%s: %s %s" % (save_file_method, tools.ustr(type(e)), tools.ustr(e) + tools.ustr(e.value))
                    raise Exception(exception_infos)
                except Exception, e:
                    exception_infos = "%s: %s %s" % (save_file_method, tools.ustr(type(e)), tools.ustr(e))
                    raise Exception(exception_infos)

    def _send_by_email(self, cr, uid, export_file, localdict):
        email_to = _render_unicode(export_file.email_to, localdict)
        email_subject = _render_unicode(export_file.email_subject, localdict)
        email_body = _render_unicode(export_file.email_body, localdict)
        email_cc = _render_unicode(export_file.email_cc, localdict)
        attachments = []
        context = localdict.get('localcontext', {})
        export = self.pool.get('ir.model.export').browse(cr, uid, context.get('attach_export_id', 0), context)
        if export_file.email_attach_export_file:
            attachments.append((localdict['filename'], localdict['file']))
        if export_file.exception_logging == 'file' and export_file.email_attach_exceptions_file:
            attachments.append((export.exceptions_filename, export.exceptions_file))
        return tools.email_send(False, email_to, email_subject, email_body, email_cc, attach=attachments)

    # ***** Execution report storage method *****

    def _save_execution_report(self, cr, uid, export_file, localdict):
        filename = localdict['filename']
        exceptions = localdict['exceptions']
        context = localdict['localcontext']
        attach_export_id = context.get('attach_export_id', False)
        summary = _render_unicode(export_file.report_summary_template, localdict)
        if exceptions and export_file.exception_logging == 'report':
            summary += "Exceptions: \n%s" % '\n'.join(exceptions)
        report_vals = {
            'name': "File Export Processing Report",
            'act_from': uid,
            'act_to': uid,
            'body': summary,
        }
        report_id = self.pool.get('res.request').create(cr, uid, report_vals, context)
        if exceptions and export_file.exception_logging == 'file':
            exceptions_filename = filename[: -filename.find('.')] + '.ERRORS' + filename[-filename.find('.'):]
            exceptions_vals = {
                'name':  exceptions_filename,
                'type': 'binary',
                'datas': base64.encodestring('\n'.join(exceptions).encode(export_file.encoding)),
                'datas_fname': exceptions_filename,
                'res_model': 'res.request',
                'res_id': report_id,
            }
            self.pool.get('ir.attachment').create(cr, uid, exceptions_vals, context)
        if attach_export_id:
            self.pool.get('ir.model.export').write(cr, uid, attach_export_id, {'report_id': report_id,
                                                                               'exception_during_last_run': bool(exceptions)}, context)
        if export_file.send_by_email:
            self._send_by_email(cr, uid, export_file, localdict)
        return True

    # ***** File generation method *****

    def _get_filename(self, cr, uid, export_file, context):
        filename = _render_unicode(export_file.filename, {
            'object': context.get('attach_export_id', False) and self.pool.get('ir.model.export').browse(cr, uid, context['attach_export_id'],
                                                                                                         context),
            'localcontext': context,
            'time': time
        }, export_file.encoding)
        extension = '.pdf'
        if export_file.extension == 'other':
            extension = export_file.extension_custom
            if extension and extension.find('.'):
                extension = '.%s' % extension
        filename += extension
        return filename

    def generate_file(self, cr, uid, export_file_id, context=None):
        """Check and lay out data, save file and produce an export processing report"""
        start_date = time.strftime('%Y-%m-%d %H:%M:%S')
        context = context or {}
        if isinstance(export_file_id, list):
            export_file_id = export_file_id[0]
        export_file = self.browse(cr, uid, export_file_id, context)
        filename = binary = ''
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
                        exceptions.append('%s, %s: %s' % (export_file.model, content_id, 'Check failed'))
                except Exception, e:
                    exceptions.append('%s, %s: %s' % (export_file.model, content_id, _get_exception_message(e)))
        context['active_ids'] = checked_content_ids
        file_content, content_exceptions = self._lay_out_data(cr, uid, export_file, context)
        exceptions += content_exceptions
        filename = self._get_filename(cr, uid, export_file, context)
        if export_file.extension == 'pdf':
            file_content = _text2pdf(file_content)
        file_content = file_content.encode(export_file.encoding, 'replace')
        self._save_file(cr, uid, export_file, filename, file_content, context)
        end_date = time.strftime('%Y-%m-%d %H:%M:%S')
        localdict = {
            'pool': self.pool,
            'cr': cr,
            'uid': uid,
            'object': export_file,
            'localcontext': context,
            'time': time,
            'datetime': datetime,
            'calendar': calendar,
            'start_time': start_date,
            'end_time': end_date,
            'filename': filename,
            'file': binary,
            'records_number': len(content_ids),
            'export_lines_number': len(content_ids) - len(exceptions),
            'exceptions_number': len(exceptions),
            'exceptions': exceptions,
        }
        return self._save_execution_report(cr, uid, export_file, localdict)
ir_model_export_file_template()


class ir_model_export_file_template_column(osv.osv):
    _name = 'ir.model.export.file_template.column'
    _description = 'Export File Template Column'

    def _has_validator(self, cr, uid, ids, name, arg, context=None):
        res = {}.fromkeys(ids, False)
        for column in self.read(cr, uid, ids, ['column_validator']):
            if column['column_validator']:
                res[column['id']] = True
        return res

    _columns = {
        'name': fields.char('Label', size=64, required=True),
        'sequence': fields.integer('Sequence', required=True),
        'export_file_template_id': fields.many2one('ir.model.export.file_template', 'Export', required=True, ondelete='cascade'),
        'value': fields.text('Value',
                             help="Use mako language with the pool, cr, uid, object, line_number, localcontext and time variables"),
        'default_value': fields.char('Default value', size=64,
                                     help="Use mako language with the pool, cr, uid, object, localcontext and time variables"),
        'not_string': fields.boolean('Not a string'),
        'column_validator': fields.text('Column validator', help="Raise an exception if validator evaluates to False: use python language "
                                                                 "with the pool, cr, uid, object, localcontext and time variables"),
        'has_validator': fields.function(_has_validator, method=True, type='boolean', string="Validator", ),
        'exception_msg': fields.char('Exception Message', size=256, translate=True,
                                     help="Use mako language with the pool, cr, uid, object, localcontext and time variables"),
        'min_width': fields.integer('Min width'),
        'fillchar': fields.char('Fillchar', size=1),
        'justify': fields.selection([
            ('ljust', 'Left'),
            ('rjust', 'Right'),
        ], 'Justify'),
        'max_width': fields.integer('Max width'),
    }

    _order = 'sequence asc'
ir_model_export_file_template_column()
