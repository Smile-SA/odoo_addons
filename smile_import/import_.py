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

import threading
import time

from osv import fields
from osv.orm import Model
import pooler
import tools

from smile_log.db_handler import SmileDBLogger


class IrModelImportTemplate(Model):
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
        context used to specify:
         - import_error_management: 'rollback_and_continue' or 'raise' (default='raise', see _process function)
         - commit_and_new_thread: True/False (default=False)
         if commit_and_new_thread = True, import_error_management is forced to rollback_and_continue

        returns a dict: {'template_id1': import_id1, ...}
        """
        if isinstance(ids, (int, long)):
            ids = [ids]
        context = context or {}
        import_obj = self.pool.get('ir.model.import')

        import_name = context.get('import_name', '')
        test_mode = context.get('test_mode', False)
        commit_and_new_thread = context.get('commit_and_new_thread', False)

        result = {}

        for template in self.browse(cr, uid, ids, context):
            import_name = import_name or template.name

            logger = SmileDBLogger(cr.dbname, 'ir.model.import.template', template.id, uid)
            import_id = import_obj.create(cr, uid, {
                'name': import_name,
                'import_tmpl_id': template.id,
                'test_mode': test_mode,
                'pid': logger.pid,
                'state': 'started',
                'from_date': time.strftime('%Y-%m-%d %H:%M:%S'),
            }, context)

            result[template.id] = import_id

            if commit_and_new_thread:
                cr.commit()
                t = threading.Thread(target=import_obj._process_with_new_cursor, args=(cr.dbname, uid, import_id, logger, context))
                t.start()
            else:
                import_obj._process_import(cr, uid, import_id, logger, context)
        return result

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

STATES = [
    ('started', 'Started'),
    ('done', 'Done'),
    ('exception', 'Exception'),
]


class IrModelImport(Model):
    _name = 'ir.model.import'
    _description = 'Import'

    _order = 'from_date desc'

    def _get_logs(self, cr, uid, ids, field_name, arg, context=None):
        result = {}
        for import_ in self.browse(cr, uid, ids, context):
            result[import_.id] = self.pool.get('smile.log').search(cr, uid, [('model_name', '=', 'ir.model.import.template'),
                                                                             ('pid', '=', import_.pid)], context=context)
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

    def _process_import(self, cr, uid, import_id, logger, context):
        """context used to specify:
         - import_error_management: 'rollback_and_continue' or 'raise' (default='raise')
        """
        assert isinstance(import_id, (int, long)), 'ir.model.import, run_import: import_id is supposed to be an integer'

        context = context and context.copy() or {}
        import_ = self.browse(cr, uid, import_id, context)
        context['test_mode'] = import_.test_mode
        context['logger'] = logger
        context['import_id'] = import_id

        error_management = context.get('import_error_management', 'raise')

        cr.execute('SAVEPOINT smile_import')
        try:
            model_obj = self.pool.get(import_.import_tmpl_id.model)
            if not model_obj:
                raise Exception('Unknown model: %s' % (import_.import_tmpl_id.model,))
            model_method = import_.import_tmpl_id.method

            getattr(model_obj, model_method)(cr, uid, context)
        except Exception, e:
            if error_management == 'rollback_and_continue':
                cr.execute("ROLLBACK TO SAVEPOINT smile_import")
                logger.info("Import rollbacking")
                return self.write(cr, uid, import_id, {'state': 'exception', 'to_date': time.strftime('%Y-%m-%d %H:%M:%S')}, context)
            else:  # import_error_management = raise
                raise e
        finally:
            if import_.test_mode:
                cr.execute("ROLLBACK TO SAVEPOINT smile_import")
                logger.info("Test mode On: Import rollbacking: %s" % (import_id,))

        try:
            return self.write(cr, uid, import_id, {'state': 'done', 'to_date': time.strftime('%Y-%m-%d %H:%M:%S')}, context)
        except Exception, e:
            logger.error("Could not mark import %s as done: %s" % (import_id, tools.ustr(repr(e))))
            raise e

    def _process_with_new_cursor(self, dbname, uid, import_id, logger, context):
        db = pooler.get_db(dbname)
        cr = db.cursor()

        context['import_error_management'] = 'rollback_and_continue'
        try:
            self._process_import(cr, uid, import_id, logger, context)
            cr.commit()
        except Exception:
            cr.rollback()
        finally:
            cr.close()


class IrModelImportLine(Model):
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
            except Exception:
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
        'sum': 1,
    }
