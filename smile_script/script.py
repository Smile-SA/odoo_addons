# -*- encoding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2013 Smile (<http://www.smile.fr>). All Rights Reserved
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

from functools import partial
import logging
from StringIO import StringIO
import time

from openerp import sql_db, SUPERUSER_ID, tools
from openerp.modules.registry import Registry
from openerp.osv import fields, osv, orm
from openerp.tools import convert_xml_import
from openerp.tools.translate import _

from smile_log.db_handler import SmileDBLogger

_logger = logging.getLogger(__name__)


def _get_exception_message(exception):
    msg = isinstance(exception, (osv.except_osv, orm.except_orm)) and exception.value or exception
    return tools.ustr(msg)


class SmileScript(orm.Model):
    _name = 'smile.script'
    _description = 'Smile Script'

    _columns = {
        'create_date': fields.datetime('Creation date', required=False, readonly=True),
        'create_uid': fields.many2one('res.users', 'Creation user', required=False, readonly=True),

        'validation_date': fields.datetime('Validation date', readonly=True),
        'validation_user_id': fields.many2one('res.users', 'Validation user', readonly=True),

        'name': fields.char('Name', size=128, required=True, readonly=True, states={'draft': [('readonly', False)]}),
        'description': fields.text('Description', required=True, readonly=True, states={'draft': [('readonly', False)]}),
        'type': fields.selection([('python', 'Python'), ('sql', 'SQL'), ('xml', 'XML')], 'Type', required=True, readonly=True,
                                 states={'draft': [('readonly', False)]}),
        'code': fields.text('Code', required=True, readonly=True, states={'draft': [('readonly', False)]}),
        'state': fields.selection([('draft', 'Draft'), ('validated', 'Validated')], 'State', required=True, readonly=True),
        'intervention_ids': fields.one2many('smile.script.intervention', 'script_id', 'Interventions', readonly=True),
        'automatic_dump': fields.boolean('Automatic dump', help='Make sure postgresql authentification is correctly set'),
        'expect_result': fields.boolean('Expect a result'),
    }

    _defaults = {
        'state': 'draft',
        'automatic_dump': True,
    }

    def _get_validated_scripts(self, cr, uid, ids, context=None):
        if isinstance(ids, (int, long)):
            ids = [ids]
        validated_scripts = []
        for script in self.browse(cr, uid, ids, context):
            if script.state != 'draft':
                validated_scripts.append(script)
        return validated_scripts

    def _can_write_after_validation(self, vals, context=None):
        keys = vals and vals.keys() or []
        for field in keys:
            if field not in ('automatic_dump', 'name'):
                return False
        return True

    def write(self, cr, uid, ids, vals, context=None):
        if not vals:
            return True
        if self._get_validated_scripts(cr, uid, ids, context) and not self._can_write_after_validation(vals, context):
            raise orm.except_orm(_('Error!'), _('You can only modify draft scripts!'))
        return super(SmileScript, self).write(cr, uid, ids, vals, context)

    def unlink(self, cr, uid, ids, context=None):
        validated_scripts = self._get_validated_scripts(cr, uid, ids, context)
        if validated_scripts:
            raise orm.except_orm(_('Error!'), _('You can only delete draft scripts!'))
        if isinstance(ids, (int, long)):
            ids = [ids]
        intervention_ids = []
        for script in self.read(cr, uid, ids, ['intervention_ids'], context):
            intervention_ids.extend(script['intervention_ids'])
        if intervention_ids:
            self.pool.get('smile.script.intervention').unlink(cr, uid, intervention_ids, context)
        return super(SmileScript, self).unlink(cr, uid, ids, context)

    def copy_data(self, cr, uid, script_id, default=None, context=None):
        default = default.copy() if default else {}
        default.update({'state': 'draft', 'intervention_ids': []})
        return super(SmileScript, self).copy_data(cr, uid, script_id, default, context)

    def validate(self, cr, uid, ids, context=None):
        validated_scripts = self._get_validated_scripts(cr, uid, ids, context)
        if validated_scripts:
            raise orm.except_orm(_('Error!'), _('You can only validate draft scripts!'))
        self.write(cr, uid, ids, {'state': 'validated', 'validation_user_id': uid,
                                  'validation_date': time.strftime('%Y-%m-%d %H:%M:%S')}, context)
        return True

    def _run(self, cr, uid, script, intervention_id, logger, context=None):
        if script.type == 'sql':
            return self._run_sql(cr, uid, script, context)
        elif script.type == 'xml':
            return self._run_xml(cr, uid, script, context)
        elif script.type == 'python':
            return self._run_python(cr, uid, script, logger, context)
        raise NotImplementedError(script.type)

    def run(self, cr, uid, ids, context=None):
        context = context or {}
        if isinstance(ids, (int, long)):
            ids = [ids]
        intervention_obj = self.pool.get('smile.script.intervention')
        for script in self.browse(cr, uid, ids, context):
            if not context.get('test_mode'):
                if script.state != 'validated':
                    raise orm.except_orm(_('Error!'), _('You can only run validated scripts!'))
                if script.automatic_dump:
                    self.dump_database(cr)
            intervention_id = intervention_obj.create(cr, uid, {'script_id': script.id, 'test_mode': context.get('test_mode')}, context)
            logger = SmileDBLogger(cr.dbname, 'smile.script.intervention', intervention_id, uid)
            if not context.get('do_not_use_new_cursor'):
                intervention_cr = sql_db.db_connect(cr.dbname).cursor()
            else:
                intervention_cr = cr
            intervention_vals = {}
            try:
                _logger.info('Running script: %s\nCode:\n%s' % (script.name.encode('utf-8'), script.code.encode('utf-8')))
                result = self._run(intervention_cr, uid, script, intervention_id, logger, context)
                if not context.get('do_not_use_new_cursor') and context.get('test_mode'):
                    logger.info('TEST MODE: Script rollbacking')
                    intervention_cr.rollback()
                elif not context.get('do_not_use_new_cursor'):
                    intervention_cr.commit()
                intervention_vals.update({'state': 'done', 'result': result})
                _logger.info('Script execution SUCCEEDED: %s\n' % (script.name.encode('utf-8'),))
            except Exception, e:
                intervention_vals.update({'state': 'exception', 'result': _get_exception_message(e)})
                _logger.error('Script execution FAILED: %s\nError:\n%s' % (script.name.encode('utf-8'), _get_exception_message(e).encode('utf-8')))
            finally:
                if not context.get('do_not_use_new_cursor'):
                    intervention_cr.close()
            intervention_vals.update({'end_date': time.strftime('%Y-%m-%d %H:%M:%S')})
            intervention_obj.write(cr, uid, intervention_id, intervention_vals, context)
        return True

    def run_test(self, cr, uid, ids, context=None):
        context_copy = context.copy() if context else {}
        context_copy['test_mode'] = True
        return self.run(cr, uid, ids, context_copy)

    def ref(self, cr, id_str):
        model_data_obj = self.pool.get('ir.model.data')
        if '.' not in id_str:
            raise ValueError("Missing '.' in reference: %s" % id_str)
        mod, id_str = id_str.split('.')
        return model_data_obj.get_object_reference(cr, SUPERUSER_ID, mod, id_str)[1]

    def _run_python(self, cr, uid, script, logger, context=None):
        localdict = {
            'pool': self.pool,
            'cr': cr,
            'uid': uid,
            'context': context,
            'ref': partial(self.ref, cr),
            'logger': logger,
            'time': time,
        }
        exec script.code in localdict
        return localdict['result'] if 'result' in localdict else 'No expected result'

    def _run_sql(self, cr, uid, script, context=None):
        cr.execute(script.code)
        if script.expect_result:
            return tools.ustr(cr.fetchall())
        return 'No expected result'

    def _run_xml(self, cr, uid, script, context=None):
        convert_xml_import(cr, __package__, StringIO(script.code.encode('utf-8')))
        return 'No expected result'

    def dump_database(self, cr):
        dump_path = tools.config.get('smile_script_dump_path')
        if not dump_path:
            raise ValueError('No value found for smile_script_dump_path')
        dbname = cr.dbname
        import netsvc
        import base64
        import os
        base_64_dump = netsvc.ExportService.getService('db').exp_dump(dbname)
        dump_data = base64.b64decode(base_64_dump)
        dump_filename = "%s_%s.dump" % (dbname, time.strftime('%Y-%m-%d %H%M%S'))
        dump_filepath = os.path.join(dump_path, dump_filename)
        with open(dump_filepath, 'w') as dump_file:
            dump_file.write(dump_data)
        _logger.info('Database %s dumped at: %s' % (dbname, dump_filepath))
        return dump_filepath


STATES = [
    ('running', 'Running'),
    ('done', 'Done'),
    ('exception', 'Exception'),
]


def state_cleaner(method):
    def wrapper(self, cr, module):
        res = method(self, cr, module)
        if self.get('smile.script.intervention'):
            cr.execute("select relname from pg_class where relname='smile_script_intervention'")
            if cr.rowcount:
                export_ids = self.get('smile.script.intervention').search(cr, SUPERUSER_ID, [('state', '=', 'running')])
                if export_ids:
                    self.get('smile.script.intervention').write(cr, SUPERUSER_ID, export_ids, {'state': 'exception'})
        return res
    return wrapper


class SmileScriptIntervention(orm.Model):
    _name = 'smile.script.intervention'
    _description = 'Smile Script Intervention'
    _rec_name = 'create_date'
    _order = 'create_date DESC'

    def __init__(self, pool, cr):
        super(SmileScriptIntervention, self).__init__(pool, cr)
        setattr(Registry, 'load', state_cleaner(getattr(Registry, 'load')))

    _columns = {
        'create_date': fields.datetime('Intervention start', required=True, readonly=True),
        'end_date': fields.datetime('Intervention end', readonly=True),
        'create_uid': fields.many2one('res.users', 'User', required=True, readonly=True),
        'script_id': fields.many2one('smile.script', 'Script', required=True, readonly=True),
        'state': fields.selection(STATES, "State", readonly=True, required=True),
        'test_mode': fields.boolean('Test Mode', readonly=True),
        'result': fields.text('Result', readonly=True),
        'log_ids': fields.one2many('smile.log', 'res_id', 'Logs', domain=[('model_name', '=', 'smile.script.intervention')], readonly=True),
    }

    _defaults = {
        'state': 'running',
    }

    def unlink(self, cr, uid, ids, context=None):
        if isinstance(ids, (int, long)):
            ids = [ids]
        for intervention in self.browse(cr, uid, ids, context):
            if not intervention.test_mode:
                raise orm.except_orm(_('Error!'), _('Intervention cannot be deleted'))
        return super(SmileScriptIntervention, self).unlink(cr, uid, ids, context)
