# -*- encoding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution    
#    Copyright (C) 2011 Smile (<http://www.smile.fr>). All Rights Reserved
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
import pooler
import tools
from tools.translate import _

from smile_log.db_handler import SmileDBLogger

class IrModelImportTemplate(osv.osv):
    _name = 'ir.model.import.template'
    _description = 'Import Template'

    _columns = {
        'name': fields.char('Name', size=64, required=True),
        'model_id': fields.many2one('ir.model', 'Object', required=True, ondelete='cascade'),
        'model': fields.related('model_id', 'model', type='char', string='Model', readonly=True),
        'method': fields.char('Method', size=64, help="Arguments passed through **kwargs", required=True),
        'import_ids': fields.one2many('ir.model.import', 'import_tmpl_id', 'Imports', readonly=True),
        'server_action_id': fields.many2one('ir.actions.server', 'Server Action'),
        'log_ids': fields.one2many('smile.log', 'res_id', 'Logs', domain=[('model_name', '=', 'ir.model.import.template')], readonly=True),
    }

    def create_import(self, cr, uid, ids, context=None):
        """
        context used to specify test_mode and import_mode
        import_mode can be:
        - same_thread_raise_error (default)
        - same_thread_rollback_and_continue
        - new_thread
        """
        if isinstance(ids, (int, long)):
            ids = [ids]
        context = context or {}
        import_obj = self.pool.get('ir.model.import')

        import_name = context.get('import_name', '')
        test_mode = context.get('test_mode', False)
        import_mode = context.get('import_mode', 'same_thread_full_rollback')

        for template in self.browse(cr, uid, ids, context):
            import_name = import_name or template.name

            logger = SmileDBLogger(cr.dbname, 'ir.model.import.template', template.id, uid)
            import_id = import_obj.create_new_cr(cr.dbname, uid, {
                                                                    'name': import_name,
                                                                    'import_tmpl_id': template.id,
                                                                    'test_mode': test_mode,
                                                                    'pid': logger.pid,
                                                                    'state': 'running',
                                                                    'from_date': time.strftime('%Y-%m-%d %H:%M:%S'),
                                                                    }, context)

            if import_mode == 'new_thread':
                t = threading.Thread(target=import_obj._process_with_new_cursor, args=(cr.dbname, uid, import_id, logger, context))
                t.start()
            else:
                cr.execute('SAVEPOINT smile_import')
                try:
                    import_obj._process_import(cr, uid, import_id, logger, context)
                except Exception, e:
                    if import_mode == 'same_thread_rollback_and_continue':
                        cr.execute("ROLLBACK TO SAVEPOINT smile_import")
                        logger.info("Import rollbacking")
                    else: #same_thread_raise_error
                        raise e
        return True

    def create_server_action(self, cr, uid, ids, context=None):
        if isinstance(ids, (int, long)):
            ids = [ids]
        model_id = self.pool.get('ir.model').search(cr, uid, [('model', '=', self._name)], limit=1, context=context)
        if model_id:
            model_id = model_id[0]
            for template in self.browse(cr, uid, ids, context):
                if not template.server_action_id:
                    vals = {
                        'name': template.name,
                        'user_id': 1,
                        'model_id': model_id,
                        'state': 'code',
                        'code': "self.pool.get('ir.model.import.template').create_import(cr, uid, %d, context)" % (template.id,),
                    }
                    server_action_id = self.pool.get('ir.actions.server').create(cr, uid, vals)
                    template.write({'server_action_id': server_action_id})
        return True
IrModelImportTemplate()

STATES = [
    ('running', 'Running'),
    ('done', 'Done'),
    ('exception', 'Exception'),
]

def state_cleaner(method):
    def state_cleaner(self, cr, mode):
        res = method(self, cr, mode)
        if self.get('ir.model.import'):
            import_ids = self.get('ir.model.import').search(cr, 1, [('state', '=', 'running')])
            if import_ids:
                self.get('ir.model.import').write(cr, 1, import_ids, {'state': 'exception'})
        return res
    return state_cleaner

class IrModelImport(osv.osv):
    _name = 'ir.model.import'
    _description = 'Import'

    _order = 'from_date desc'

    def __init__(self, pool, cr):
        super(IrModelImport, self).__init__(pool, cr)
        setattr(osv.osv_pool, 'init_set', state_cleaner(getattr(osv.osv_pool, 'init_set')))

    def _get_logs(self, cr, uid, ids, field_name, arg, context=None):
        result = {}
        for import_ in self.browse(cr, uid, ids, context):
            result[import_.id] = self.pool.get('smile.log').search(cr, uid, [('model_name', '=', 'ir.model.import.template'), ('pid', '=', import_.pid)], context=context)
        return result

    _columns = {
        'name': fields.char('Name', size=64, readonly=True),
        'import_tmpl_id': fields.many2one('ir.model.import.template', 'Template', readonly=True, required=True, ondelete='cascade'),
        'from_date': fields.datetime('From date', readonly=True),
        'to_date': fields.datetime('To date', readonly=True),
        'test_mode': fields.boolean('Test Mode', readonly=True),
        'pid': fields.integer('PID', readonly=True),
        'log_ids': fields.function(_get_logs, method=True, type='one2many', relation='smile.log', string="Logs"),
        'state': fields.selection(STATES, "State", readonly=True, required=True,),
    }

    def create_new_cr(self, dbname, uid, vals, context):
        db = pooler.get_db(dbname)
        cr = db.cursor()

        try:
            import_id = self.pool.get('ir.model.import').create(cr, uid, vals, context)
            cr.commit()
        finally:
            cr.close()

        return import_id

    def write_new_cr(self, dbname, uid, ids, vals, context):
        db = pooler.get_db(dbname)
        cr = db.cursor()

        try:
            result = self.pool.get('ir.model.import').write(cr, uid, ids, vals, context)
            cr.commit()
        finally:
            cr.close()

        return result

    def _process_import(self, cr, uid, import_id, logger, context):
        assert isinstance(import_id, (int, long)), 'ir.model.import, run_import: import_id is supposed to be an integer'

        context = context and context.copy() or {}
        import_ = self.browse(cr, uid, import_id, context)
        context['test_mode'] = import_.test_mode
        context['logger'] = logger
        context['import_id'] = import_id

        cr.execute("SAVEPOINT smile_import_test_mode")
        try:
            model_obj = self.pool.get(import_.import_tmpl_id.model)
            if not model_obj:
                raise Exception('Unknown model: %s' % (import_.import_tmpl_id.model,))
            model_method = import_.import_tmpl_id.method

            getattr(model_obj, model_method)(cr, uid, context)
        except Exception, e:
            logger.critical("Import failed: %s" % (tools.ustr(repr(e))))
            self.write_new_cr(cr.dbname, uid, import_id, {'state': 'exception', 'to_date': time.strftime('%Y-%m-%d %H:%M:%S')}, context)
            raise e
        finally:
            if import_.test_mode:
                cr.execute("ROLLBACK TO SAVEPOINT smile_import_test_mode")
                logger.info("Import rollbacking: %s" % (import_id,))
        try:
            self.write(cr, uid, import_id, {'state': 'done', 'to_date': time.strftime('%Y-%m-%d %H:%M:%S')}, context)
        except Exception, e:
            logger.error("Could not mark import %s as done: %s" % (import_id, tools.ustr(repr(e))))
            raise e

    def _process_with_new_cursor(self, dbname, uid, import_id, logger, context=None):
        db = pooler.get_db(dbname)
        cr = db.cursor()

        try:
            self._process_import(cr, uid, import_id, logger, context)
            cr.commit()
        except Exception, e:
            cr.rollback()
        finally:
            cr.close()

IrModelImport()

class IrModelImportLine(osv.osv):
    _name = 'ir.model.import.line'
    _description = 'Import Line'
    _rec_name = 'import_id'


    def _get_resource_label(self, cr, uid, ids, name, args, context=None):
        """ get the resource label using the name_get function of the imported model
        group the line res_id by model before performing the name_get call
        """
        model_to_res_ids = {}
        line_id_to_res_id_model = {}
        for line in self.browse(cr, uid, ids, context):
            model_to_res_ids.setdefault(line.import_id.model, []).append(line.res_id)
            line_id_to_res_id_model[line.id] = (line.res_id, line.import_id.model)

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
        'import_id': fields.many2one('ir.model.import', 'Import', required=True, ondelete='cascade'),
        'model': fields.char('Model', size=64),
        'sum': fields.integer('Sum'),
        'res_id': fields.integer('Resource ID', required=True),
        'res_label': fields.function(_get_resource_label, method=True, type='char', size=256, string="Resource label"),
    }

    _order = 'import_id desc'
    
    _defaults = {
        'sum':1,
    }
IrModelImportLine()
