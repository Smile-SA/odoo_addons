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

import threading, time

from osv import osv, fields
import tools, pooler

from smile_log.db_handler import SmileDBLogger

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
        """
        context used to specify export_mode
        export_mode can be:
        - same_thread_raise_error (default)
        - same_thread_rollback_and_continue
        - new_thread
        """
        if isinstance(ids, (int, long)):
            ids = [ids]
        context = context or {}
        context.setdefault('export_mode', 'same_thread_full_rollback')
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
                export_ids.append(export_pool.create_new_cr(cr.dbname, uid, {
                    'export_tmpl_id': export_template.id,
                    'state': 'running',
                    'line_ids': [(0, 0, {'res_id': res_id}) for res_id in export_res_ids],
                    'offset': index + 1,
                }, context))

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

STATES = [
    ('running', 'Running'),
    ('done', 'Done'),
    ('exception', 'Exception'),
]

def state_cleaner(method):
    def state_cleaner(self, cr, mode):
        res = method(self, cr, mode)
        if self.get('ir.model.export'):
            export_ids = self.get('ir.model.export').search(cr, 1, [('state', '=', 'running')])
            if export_ids:
                self.get('ir.model.export').write(cr, 1, export_ids, {'state': 'exception'})
        return res
    return state_cleaner

class ir_model_export(osv.osv):
    _name = 'ir.model.export'
    _description = 'Export'
    _rec_name = 'export_tmpl_id'

    def __init__(self, pool, cr):
        super(ir_model_export, self).__init__(pool, cr)
        setattr(osv.osv_pool, 'init_set', state_cleaner(getattr(osv.osv_pool, 'init_set')))

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
        'log_ids': fields.one2many('smile.log', 'res_id', 'Logs', domain=[('model_name', '=', 'ir.model.export')], readonly=True),
        'state': fields.selection(STATES, "State", readonly=True, required=True,),
        'exception': fields.text('Exception'),
    }

    _order = 'create_date desc'

    def create_new_cr(self, dbname, uid, vals, context):
        db = pooler.get_db(dbname)
        cr = db.cursor()

        try:
            export_id = self.pool.get('ir.model.export').create(cr, uid, vals, context)
            cr.commit()
        finally:
            cr.close()

        return export_id

    def write_new_cr(self, dbname, uid, ids, vals, context):
        db = pooler.get_db(dbname)
        cr = db.cursor()

        try:
            result = self.pool.get('ir.model.export').write(cr, uid, ids, vals, context)
            cr.commit()
        finally:
            cr.close()

        return result

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
        """
        context used to specify export_mode
        export_mode can be:
        - same_thread_raise_error (default)
        - same_thread_rollback_and_continue
        - new_thread
        """
        if isinstance(ids, (int, long)):
            ids = [ids]
        context = context or {}
        export_mode = context.get('export_mode', 'same_thread_full_rollback')

        for export_id in ids:
            logger = SmileDBLogger(cr.dbname, 'ir.model.export', export_id, uid)
            if export_mode == 'new_thread':
                t = threading.Thread(target=self._generate_with_new_cursor, args=(cr.dbname, uid, export_id, logger, context))
                t.start()
            else:
                cr.execute('SAVEPOINT smile_export')
                try:
                    self._generate(cr, uid, export_id, logger, context)
                except Exception, e:
                    if export_mode == 'same_thread_rollback_and_continue':
                        cr.execute("ROLLBACK TO SAVEPOINT smile_export")
                        logger.info("Export rollbacking")
                    else: #same_thread_raise_error
                        raise e
        return True

    def _generate_with_new_cursor(self, dbname, uid, export_id, logger, context):
        try:
            db = pooler.get_db(dbname)
        except:
            return False
        cr = db.cursor()
        try:
            self._generate(cr, uid, export_id, logger, context)
        finally:
            cr.close()
        return

    def _generate(self, cr, uid, export_id, logger, context=None):
        """Call export method and action
        Catch and log exceptions"""
        assert isinstance(export_id, (int, long)), 'ir.model.export, _generate: export_id is supposed to be an integer'

        context = context and context.copy() or {}
        export = self.browse(cr, uid, export_id, context)
        context['logger'] = logger
        context['export_id'] = export.id

        try:
            if export.line_ids:
                res_ids = [line.res_id for line in export.line_ids]
                logger.info('Export start')
                self._run_actions(cr, uid, export, res_ids, context)
                logger.time_info('Export done')
        except Exception, e:
            logger.critical("Export failed: %s" % (tools.ustr(repr(e))))
            self.write_new_cr(cr.dbname, uid, export_id, {'state': 'exception',
                                                          'to_date': time.strftime('%Y-%m-%d %H:%M:%S'),
                                                          'exception': isinstance(e, osv.except_osv) and e.value or e, }, context)
            raise e

        try:
            self.write(cr, uid, export_id, {'state': 'done', 'to_date': time.strftime('%Y-%m-%d %H:%M:%S')}, context)
        except Exception, e:
            logger.error("Could not mark export %s as done: %s" % (export_id, tools.ustr(repr(e))))
            raise e
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
