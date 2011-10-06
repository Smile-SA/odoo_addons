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

import threading

from osv import osv, fields
import pooler

from export_handler import SmileExportLogger

class ir_model_export_template(osv.osv):
    _name = 'ir.model.export.template'
    _description = 'Export Template'

    _columns = {
        'name': fields.char('Name', size=64, required=True),
        'model_id': fields.many2one('ir.model', 'Object', domain=[('osv_memory', '=', False)], required=True, ondelete='cascade'),
        'model': fields.related('model_id', 'model', type='char', string='Model', readonly=True),
        'domain': fields.char('Domain', size=255),
        'limit': fields.integer('Limit'),
        'max_offset': fields.integer('Max Offset'),
        'order': fields.char('Order by', size=64),
        'unique': fields.boolean('Unique', help="If unique, each instance is exported only once"),
        'method': fields.char('Method', size=64, help="Indicate a method with a signature equals to (self, cr, uid, ids, *args, context=None)"),
        'action_id': fields.many2one('ir.actions.server', 'Action'),
        'export_ids': fields.one2many('ir.model.export', 'export_tmpl_id', 'Exports'),
        'cron_id': fields.many2one('ir.cron', 'Scheduled Action'),
        'client_action_id': fields.many2one('ir.values', 'Client Action'),
        'client_action_server_id': fields.many2one('ir.actions.server', 'Client Action Server'),
    }

    _defaults = {
        'domain': '[]',
    }

    def _build_domain(self, cr, uid, export_template, context):
        domain = []
        export_line_pool = self.pool.get('ir.model.export.line')
        if not context.get('bypass_domain', False):
            domain += eval(export_template.domain)
        else:
            domain += [('id', 'in', context.get('active_ids', []))]
        if export_template.unique:
            export_line_ids = export_line_pool.search(cr, uid, [('export_id.export_tmpl_id.model_id', '=', export_template.model_id.id)])
            exported_object_ids = [line['res_id'] for line in export_line_pool.read(cr, uid, export_line_ids, ['res_id'])]
            domain += [('id', 'not in', exported_object_ids)]
        return domain

    def create_export(self, cr, uid, ids, context=None):
        if isinstance(ids, (int, long)):
            ids = [ids]
        context = context or {}
        export_pool = self.pool.get('ir.model.export')
        export_ids = []

        for export_template in self.browse(cr, uid, ids, context):
            total_offset = 1
            domain = self._build_domain(cr, uid, export_template, context)
            res_ids = self.pool.get(export_template.model).search(cr, uid, domain, context=context)
            res_ids_list = [res_ids]

            if export_template.limit:
                i = 0
                while(res_ids[i:i + export_template.limit]):
                    if export_template.max_offset and i == export_template.max_offset * export_template.limit:
                        break
                    res_ids_list.append(res_ids[i:i + export_template.limit])
                    i += export_template.limit

            for index, export_res_ids in enumerate(res_ids_list):
                export_ids.append(export_pool.create(cr, uid, {
                    'export_tmpl_id': export_template.id,
                    'line_ids': [(0, 0, {'res_id': res_id}) for res_id in export_res_ids],
                    'offset': index + 1,
                }, context))

        context['same_thread'] = True
        cr.commit()
        export_pool.generate(cr, uid, export_ids, context)
        return True

    def create_cron(self, cr, uid, ids, context=None):
        if isinstance(ids, (int, long)):
            ids = [ids]
        for template in self.browse(cr, uid, ids, context):
            if not template.cron_id:
                vals = {
                    'name': template.name,
                    'user_id': 1,
                    'model': self._name,
                    'function': 'create_export',
                    'args': '(%d,)' % template.id,
                    'numbercall':-1,
                }
                cron_id = self.pool.get('ir.cron').create(cr, uid, vals)
                template.write({'cron_id': cron_id})
        return True

    def create_client_action(self, cr, uid, ids, context=None):
        if isinstance(ids, (int, long)):
            ids = [ids]
        for template in self.browse(cr, uid, ids, context):
            if not template.client_action_id:
                vals = {
                    'name': template.name,
                    'model_id': template.model_id.id,
                    'state': 'code',
                    'code': """context['bypass_domain'] = True
self.pool.get('ir.model.export.template').create_export(cr, uid, %d, context)""" % (template.id,),
                }
                server_action_id = self.pool.get('ir.actions.server').create(cr, uid, vals, context)
                vals2 = {
                    'name': template.name,
                    'object': True,
                    'model_id': template.model_id.id,
                    'model': template.model_id.model,
                    'key2': 'client_action_multi',
                    'value': 'ir.actions.server,%d' % server_action_id,
                }
                client_action_id = self.pool.get('ir.values').create(cr, uid, vals2, context)
                template.write({'client_action_id': client_action_id, 'client_action_server_id': server_action_id, })
        return True
ir_model_export_template()

class ir_model_export(osv.osv):
    _name = 'ir.model.export'
    _description = 'Export'
    _rec_name = 'export_tmpl_id'

    _columns = {
        'export_tmpl_id': fields.many2one('ir.model.export.template', 'Template', required=True, ondelete='cascade'),
        'model_id': fields.related('export_tmpl_id', 'model_id', type='many2one', relation='ir.model', string='Object', readonly=True),
        'model': fields.related('model_id', 'model', type='char', string='Model', readonly=True),
        'domain': fields.related('export_tmpl_id', 'domain', type='char', string='Domain', readonly=True),
        'limit': fields.related('export_tmpl_id', 'limit', type='integer', string='Limit', readonly=True),
        'offset': fields.integer('Offset'),
        'order': fields.related('export_tmpl_id', 'order', type='char', string='Order by', readonly=True),
        'unique': fields.related('export_tmpl_id', 'unique', type='boolean', string='Unique', readonly=True),
        'method': fields.related('export_tmpl_id', 'method', type='char', string='Method', readonly=True),
        'action_id': fields.related('export_tmpl_id', 'action_id', type='many2one', relation='ir.actions.server', string='Action', readonly=True),
        'create_date': fields.datetime('Creation Date', readonly=True),
        'create_uid': fields.many2one('res.users', 'Creation User', readonly=True),
        'line_ids': fields.one2many('ir.model.export.line', 'export_id', 'Lines'),
        'log_ids': fields.one2many('ir.model.export.log', 'export_id', 'Logs', readonly=True),
        'state': fields.selection([
            ('draft', 'Draft'),
            ('running', 'Running'),
            ('done', 'Done'),
            ('exception', 'Exception'),
        ], 'State'),
        'exception': fields.text('Exception'),
    }

    _order = 'create_date desc'

    _defaults = {
        'state': 'draft',
    }

    def _run_actions(self, cr, uid, export, res_ids=[], context=None):
        """Execute export method and action"""
        context = context or {}
        if export.method:
            getattr(self.pool.get(export.model_id.model), export.method)(cr, uid, res_ids, context=context)
        if export.action_id:
            for res_id in res_ids:
                context['active_id'] = res_id
                self.pool.get('ir.actions.server').run(cr, uid, export.action_id.id, context=context)

    def generate(self, cr, uid, ids, context=None):
        """Create a new thread dedicated to export generation"""
        context = context or {}
        if context.get('same_thread', False):
            return self._generate(cr, uid, ids, context)
        threaded_run = threading.Thread(target=self._generate_with_new_cursor, args=(cr.dbname, uid, ids, context))
        threaded_run.start()
        return True

    def _generate_with_new_cursor(self, dbname, uid, ids, context):
        try:
            db = pooler.get_db(dbname)
        except:
            return False
        cr = db.cursor()
        try:
            self._generate(cr, uid, ids, context)
        finally:
            cr.close()
        return

    def _generate(self, cr, uid, ids, context=None):
        """Call export method and action
        Catch and log exceptions"""
        if isinstance(ids, (int, long)):
            ids = [ids]
        for export in self.browse(cr, uid, ids, context):
            is_running = (export.state == 'running')
            logger = SmileExportLogger(uid, export.id)
            context['export_id'] = export.id
            try:
                if not is_running:
                    if export.line_ids:
                        res_ids = [line.res_id for line in export.line_ids]
                        logger.info('Export start')
                        export.write({'state': 'running'}, context)
                        cr.commit()
                        self._run_actions(cr, uid, export, res_ids, context)
                        logger.time_info('Export done')
                    export.write({'state': 'done'}, context)
            except Exception, e:
                cr.rollback()
                logger.critical(isinstance(e, osv.except_osv) and e.value or e)
                export.write({
                    'state': 'exception',
                    'exception': isinstance(e, osv.except_osv) and e.value or e,
                }, context)
            finally:
                cr.commit()
        return True
ir_model_export()

class ir_model_export_line(osv.osv):
    _name = 'ir.model.export.line'
    _description = 'Export Line'
    _rec_name = 'export_id'


    def _get_resource_label(self, cr, uid, ids, name, args, context=None):
        """ get the resource label using the name_get function of the exported model
        group the line res_id by model before performing the name_get call
        """
        model_to_res_ids = {}
        line_id_to_res_id_model = {}
        for line in self.browse(cr, uid, ids, context):
            model_to_res_ids.setdefault(line.export_id.model, []).append(line.res_id)
            line_id_to_res_id_model[line.id] = (line.res_id, line.export_id.model)

        buf_result = {}
        for model, res_ids in model_to_res_ids.iteritems():
            name_get_result = []
            try:
                name_get_result = self.pool.get(model).name_get(cr, uid, res_ids, context)
            except:
                name_get_result = [(res_id, "name_get error") for res_id in res_ids]
            for res_id, name in name_get_result:
                buf_result[(res_id, model)] = name

        result = {}
        for line_id in line_id_to_res_id_model:
            result[line_id] = buf_result[line_id_to_res_id_model[line_id]]
        return result

    _columns = {
        'export_id': fields.many2one('ir.model.export', 'Export', required=True, ondelete='cascade'),
        'res_id': fields.integer('Resource ID', required=True),
        'res_label': fields.function(_get_resource_label, method=True, type='char', size=256, string="Resource label"),
    }
ir_model_export_line()

class ir_model_export_log(osv.osv):
    _name = 'ir.model.export.log'
    _description = 'Export Log'
    _rec_name = 'message'

    _order = 'create_date desc'

    _columns = {
        'create_date': fields.datetime('Date', readonly=True),
        'export_id': fields.many2one('ir.model.export', 'Export', readonly=True, ondelete='cascade'),
        'level': fields.char('Level', size=16, readonly=True),
        'message': fields.text('Message', readonly=True),
    }
ir_model_export_log()
