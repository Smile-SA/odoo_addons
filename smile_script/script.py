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

import time
import logging
from functools import partial

from osv import fields, osv
import tools
from tools.translate import _


LOGGER = logging.getLogger(__name__)


class SmileScript(osv.osv):
    _name = 'smile.script'
    _description = 'Smile Script'

    _columns = {
        'create_date': fields.datetime('Creation date', required=True, readonly=True),
        'create_uid': fields.many2one('res.users', 'Creation user', required=True, readonly=True),

        'validation_date': fields.datetime('Validation date', readonly=True),
        'validation_user_id': fields.many2one('res.users', 'Validation user', readonly=True),

        'name': fields.char('Name', size=64, required=True, readonly=True,
                            states={'draft': [('readonly', False)]}),
        'description': fields.text('Description', required=True, readonly=True,
                                   states={'draft': [('readonly', False)]}),
        'type': fields.selection([('sql', 'SQL'),
                                  ('python', 'Python')], 'Type', required=True,
                                 readonly=True, states={'draft': [('readonly', False)]}),
        'code': fields.text('Code', required=True, readonly=True,
                            states={'draft': [('readonly', False)]}),
        'state': fields.selection([('draft', 'Draft'),
                                   ('validated', 'Validated')], 'State',
                                  required=True, readonly=True),
        'automatic_dump': fields.boolean('Automatic dump', readonly=True,
                                         states={'draft': [('readonly', False)]},
                                         help='Make sure postgresql authentification is correctly set'),
        'intervention_ids': fields.one2many('smile.script.intervention', 'script_id',
                                            'Interventions', readonly=True),
    }

    _defaults = {
        'state': 'draft',
        'automatic_dump': True,
    }

    def _get_validated_scripts(self, cr, uid, ids, context):
        if isinstance(ids, (int, long)):
            ids = [ids]
        validated_scripts = []
        for script in self.browse(cr, uid, ids, context):
            if script.state != 'draft':
                validated_scripts.append(script)
        return validated_scripts

    def write(self, cr, uid, ids, vals, context=None):
        validated_scripts = self._get_validated_scripts(cr, uid, ids, context)
        if validated_scripts:
            raise osv.except_osv(_('Error!'),
                                 _('You can only modify draft scripts!'))
        return super(SmileScript, self).write(cr, uid, ids, vals, context)

    def unlink(self, cr, uid, ids, context=None):
        validated_scripts = self._get_validated_scripts(cr, uid, ids, context)
        if validated_scripts:
            raise osv.except_osv(_('Error!'),
                                 _('You can only delete draft scripts!'))
        return super(SmileScript, self).unlink(cr, uid, ids, context)

    def copy_data(self, cr, uid, script_id, default=None, context=None):
        default = default.copy() if default else {}
        default.update({
            'state': 'draft',
            'intervention_ids': [],
        })
        return super(SmileScript, self).copy_data(cr, uid, script_id, default, context)

    def validate(self, cr, uid, ids, context=None):
        validated_scripts = self._get_validated_scripts(cr, uid, ids, context)
        if validated_scripts:
            raise osv.except_osv(_('Error!'),
                                 _('You can only validate draft scripts!'))
        self.write(cr, uid, ids, {'state': 'validated',
                                  'validation_user_id': uid,
                                  'validation_date': time.strftime('%Y-%m-%d %H:%M:%S'), }, context)
        return True

    def run(self, cr, uid, ids, context=None):
        if isinstance(ids, (int, long)):
            ids = [ids]
        intervention_obj = self.pool.get('smile.script.intervention')
        for script in self.browse(cr, uid, ids, context):
            if script.state != 'validated':
                raise osv.except_osv(_('Error!'),
                                     _('You can only run validated scripts!'))
            if script.automatic_dump:
                self.dump_database(cr)
            LOGGER.info('Running script: {}\nCode:\n{}'.format(script.name, script.code))
            intervention_id = intervention_obj.create(cr, uid, {'script_id': script.id}, context)
            if script.type == 'sql':
                self._run_sql(cr, uid, script, intervention_id, context)
            elif script.type == 'python':
                self._run_python(cr, uid, script, intervention_id, context)
            else:
                raise NotImplementedError(script.type)
            intervention_obj.write(cr, uid, intervention_id, {'end_date': time.strftime('%Y-%m-%d %H:%M:%S')},
                                   context)
        return True

    def _run_sql(self, cr, uid, script, intervention_id, context=None):
        cr.execute(script.code)

    def ref(self, cr, id_str):
        model_data_obj = self.pool.get('ir.model.data')
        if '.' not in id_str:
            raise ValueError("Missing '.' in reference: %s" % id_str)
        mod, id_str = id_str.split('.')
        return model_data_obj.get_object_reference(cr, 1, mod, id_str)[1]

    def _run_python(self, cr, uid, script, intervention_id, context=None):
        exec_locals = {
            'cr': cr,
            'uid': uid,
            'pool': self.pool,
            'context': context,
            'ref': partial(self.ref, cr),
            'logger': LOGGER,
            'intervention_id': intervention_id,
        }
        exec(script.code, exec_locals)

    def dump_database(self, cr):
        dump_path = tools.config.get('smile_script_dump_path')
        if not dump_path:
            raise ValueError('No value found for smile_script_dump_path')
        dbname = cr.dbname
        import netsvc
        import base64
        import os.path
        base_64_dump = netsvc.ExportService.getService('db').exp_dump(dbname)
        dump_data = base64.b64decode(base_64_dump)
        dump_filename = "{}_{}.dump".format(dbname, time.strftime('%Y-%m-%d %H%M%S'))
        dump_filepath = os.path.join(dump_path, dump_filename)
        with open(dump_filepath, 'w') as dump_file:
            dump_file.write(dump_data)
        LOGGER.info('Database %s dumped at: %s' % (dbname, dump_filepath))
        return dump_filepath

SmileScript()


class SmileScriptIntervention(osv.osv):
    _name = 'smile.script.intervention'
    _description = 'Smile script intervention'
    _order = 'create_date DESC'

    _columns = {
        'create_date': fields.datetime('Intervention start', required=True, readonly=True),
        'end_date': fields.datetime('Intervention end', readonly=True),
        'create_uid': fields.many2one('res.users', 'User', required=True, readonly=True),
        'script_id': fields.many2one('smile.script', 'Script', required=True, readonly=True),
        'result': fields.text('Result', readonly=True),
    }

    def unlink(self, cr, uid, ids, context=None):
        raise osv.except_osv(_('Error!'), _('Intervention should not be deleted'))

SmileScriptIntervention()
