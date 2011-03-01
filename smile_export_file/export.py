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

from osv import osv, fields

class ir_model_export_template(osv.osv):
    _inherit = 'ir.model.export.template'

    _columns = {
        'export_file_template_id': fields.many2one('ir.model.export.file_template', 'File Template'),
        'record_ids': fields.char('Record Ids', size=256, help="Provide the field name that the record ids refer to for the records to export. If it is empty it will refer to the active ids of the object."),
    }
ir_model_export_template()

class ir_model_export(osv.osv):
    _inherit = 'ir.model.export'

    def _get_last_attachments(self, cr, uid, ids, name, args, context=None):
        res = {}
        for export in self.read(cr, uid, ids, ['report_id']):
            res[export['id']] = {'attachment_id': False, 'exceptions_attachment_id': False}
            attachment_ids = self.pool.get('ir.attachment').search(cr, uid, [('res_model', '=', self._name), ('res_id', '=', export['id'])], limit=1, order='create_date desc')
            if attachment_ids:
                res[export['id']]['attachment_id'] = attachment_ids[0]
            if export['report_id']:
                exceptions_attachment_ids = self.pool.get('ir.attachment').search(cr, uid, [('res_model', '=', 'res.request'), ('res_id', '=', export['report_id'][0])], limit=1, order='create_date desc')
                if exceptions_attachment_ids:
                    res[export['id']]['exceptions_attachment_id'] = exceptions_attachment_ids[0]
        return res

    _columns = {
        'export_file_template_id': fields.related('export_tmpl_id', 'export_file_template_id',
            type='many2one', relation='ir.model.export.file_template', string='File Template', readonly=True),
        'record_ids': fields.related('export_tmpl_id', 'record_ids',
            type='char', string='Record Ids', readonly=True),
        'report_id': fields.many2one('res.request', string='Report', readonly=True),
        'report_summary': fields.related('report_id', 'body',
            type='char', string='Report', readonly=True),
        'attachment_id': fields.function(_get_last_attachments, method=True, type='many2one', relation='ir.attachment', string='Attachment', store=False, multi='report'),
        'file': fields.related('attachment_id', 'datas', type='binary', string="File"),
        'filename': fields.related('attachment_id', 'datas_fname', type='char', string="Filename"),
        'exceptions_attachment_id': fields.function(_get_last_attachments, method=True, type='many2one', relation='ir.attachment', string='Exceptions', store=False, multi='report'),
        'exceptions_file': fields.related('exceptions_attachment_id', 'datas', type='binary', string="Exceptions File"),
        'exceptions_filename': fields.related('exceptions_attachment_id', 'datas_fname', type='char', string="Exceptions Filename"),
    }

    def _run_actions(self, cr, uid, export, object_ids=[], context=None):
        super(ir_model_export, self)._run_actions(cr, uid, export, object_ids, context)
        if export.export_file_template_id:
            context = context or {}
            context['active_ids'] = []
            if export.model == export.export_file_template_id.model:
                context['active_ids'] = object_ids
            else:
                for object in self.pool.get(export.model).browse(cr, uid, object_ids):
                    record_ids = eval(export.record_ids, {'object': object})
                    if isinstance(record_ids, (int, long)):
                        record_ids = [record_ids]
                    context['active_ids'] += record_ids
            context['attach_export_id'] = export.id
            self.pool.get('ir.model.export.file_template').generate_file(cr, uid, export.export_file_template_id.id, context)
ir_model_export()
