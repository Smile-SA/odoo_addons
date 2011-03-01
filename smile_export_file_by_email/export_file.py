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

from smile_export_file.export_file import _render_unicode
from osv import osv, fields
import tools

class ir_model_export_file_template(osv.osv):
    _inherit = 'ir.model.export.file_template'

    _columns = {
        'send_by_email': fields.boolean('Send by email'),
        'email_to': fields.char('To', size=128),
        'email_cc': fields.char('CC', size=128),
        'email_subject': fields.char('Subject', size=256),
        'email_body': fields.text('Body'),
        'email_attach_export_file': fields.boolean('Attach export file'),
        'email_attach_exceptions_file': fields.boolean('Attach exceptions file'),
    }

    _defaults = {
        'email_attach_export_file': lambda * a: True,
    }

    def _send_by_email(self, cr, uid, export_file, localdict):
        email_to = _render_unicode(export_file.email_to, localdict)
        email_subject = _render_unicode(export_file.email_subject, localdict)
        email_body = _render_unicode(export_file.email_body, localdict)
        email_cc = _render_unicode(export_file.email_cc, localdict)
        attachments = []
        context = localdict.get('context', {})
        export = self.pool.get('ir.model.export').browse(cr, uid, context.get('attach_export_id', 0), context)
        if export_file.email_attach_export_file:
            attachments.append((localdict['filename'], localdict['file']))
        if export_file.exception_logging == 'file' and export_file.email_attach_exceptions_file:
            attachments.append((export.exceptions_filename, export.exceptions_file))
        return tools.email_send(False, email_to, email_subject, email_body, email_cc, attach=attachments)

    def _save_execution_report(self, cr, uid, export_file, localdict):
        res = super(ir_model_export_file_template, self)._save_execution_report(cr, uid, export_file, localdict)
        if export_file.send_by_email:
            self._send_by_email(cr, uid, export_file, localdict)
        return res
ir_model_export_file_template()
