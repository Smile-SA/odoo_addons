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

from osv import fields
from osv.orm import Model, except_orm
import pooler
import tools
from tools.translate import _

from smile_log.db_handler import SmileDBLogger


def _get_exception_message(exception):
    msg = isinstance(exception, except_orm) and exception.value or exception
    return tools.ustr(msg)


class ir_model_export_template(Model):
    _name = 'ir.model.export.template'
    _description = 'Export Template'

    _columns = {
        'name': fields.char('Name', size=64, required=True),
        'model_id': fields.many2one('ir.model', 'Object', domain=[('osv_memory', '=', False)], required=True, ondelete='cascade'),
        'model': fields.related('model_id', 'model', type='char', string='Model', readonly=True),
        'filter_type': fields.selection([('domain', 'Domain'), ('method', 'Method')], string="Filter method", required=True,),
        'domain': fields.char('Filter domain', size=256),
        'filter_method': fields.char('Filter method', size=64, help="signature: method(cr, uid, context)"),
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
        'log_ids': fields.one2many('smile.log', 'res_id', 'Logs', domain=[('model_name', '=', 'ir.model.export.template')], readonly=True),
        'force_execute_action': fields.boolean('Force execute action', help="Even if there are no resources to export"),
    }

    _defaults = {
        'domain': '[]',
        'filter_type': 'domain',
    }

    def _get_res_ids(self, cr, uid, template, context):
        context = context or {}
        res_ids = context.get('resource_ids_to_export', [])
        model_obj = self.pool.get(template.model)
        if not model_obj:
            raise except_orm(_('Error'), _("Unknown object: %s") % (template.model,))
        if template.filter_type == 'domain':
            domain = eval(template.domain)
            if res_ids:
                domain.append(('id', 'in', res_ids))
            res_ids = model_obj.search(cr, uid, domain, context=context)
        elif template.filter_type == 'method':
            if not (template.filter_method and hasattr(model_obj, template.filter_method)):
                raise except_orm(_('Error'), _("Can't find method: %s on object: %s") % (template.filter_method, template.model))
            context['ir_model_export_template_id'] = template.id
            res_ids2 = getattr(model_obj, template.filter_method)(cr, uid, context)
            return res_ids and list(set(res_ids) & set(res_ids2)) or res_ids2
        return res_ids

    def get_exported_res_ids(self, cr, uid, export_template_id, context):
        export_line_ids = self.pool.get('ir.model.export.line').search(cr, uid, [
            ('export_id.export_tmpl_id', '=', export_template_id),
        ], context=context)
        return [line['res_id'] for line in self.pool.get('ir.model.export.line').read(cr, uid, export_line_ids, ['res_id'], context)]

    def unlink_res_ids(self, cr, uid, ids, model, res_ids, context):
        unlink_line_ids = []
        for template in self.browse(cr, uid, ids, context):
            if template.model != model:
                raise except_orm(_('Error'), _("unlink_res_ids: model(%s) does not match template model (%s, %s)")
                                 % (model, template.id, template.model))
            export_line_ids = self.pool.get('ir.model.export.line').search(cr, uid, [('export_id.export_tmpl_id', '=', template.id),
                                                                                     ('res_id', 'in', res_ids),
                                                                                     ], context=context)
            if export_line_ids:
                real_res_ids = [line['res_id'] for line in self.pool.get('ir.model.export.line').read(cr, uid, export_line_ids, ['res_id'], context)]
                logger = SmileDBLogger(cr.dbname, 'ir.model.export.template', template.id, uid)
                logger.info('Unlinking model:%s, res_ids: %s - real_res_ids found: %s' % (model, res_ids, real_res_ids))
                self.pool.get('ir.model.export.line').unlink(cr, uid, export_line_ids, context)
                unlink_line_ids.extend(export_line_ids)
        return unlink_line_ids

    def create_export(self, cr, uid, ids, context=None):
        """
        some options can be set in the context, see 'ir.model.export' generate function
        """
        if isinstance(ids, (int, long)):
            ids = [ids]
        export_pool = self.pool.get('ir.model.export')
        export_ids = []

        for export_template in self.browse(cr, uid, ids, context):
            res_ids = self._get_res_ids(cr, uid, export_template, context)
            if export_template.unique:
                old_res_ids = self.get_exported_res_ids(cr, uid, export_template.id, context)
                res_ids = list(set(res_ids) - set(old_res_ids))

            res_ids_list = []
            if export_template.limit:
                i = 0
                while(res_ids[i:i + export_template.limit]):
                    if export_template.max_offset and i == export_template.max_offset * export_template.limit:
                        break
                    res_ids_list.append(res_ids[i:i + export_template.limit])
                    i += export_template.limit
            else:
                res_ids_list = [res_ids]

            for index, export_res_ids in enumerate(res_ids_list):
                export_ids.append(export_pool.create(cr, uid, {
                    'export_tmpl_id': export_template.id,
                    'state': 'started',
                    'line_ids': [(0, 0, {'res_id': res_id}) for res_id in export_res_ids],
                    'offset': index + 1,
                }, context))

        export_pool.generate(cr, uid, export_ids, context)
        return export_ids

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
                    'numbercall': -1,
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
context['resource_ids_to_export'] = context.get('active_ids', [])
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


STATES = [
    ('started', 'Started'),
    ('done', 'Done'),
    ('exception', 'Exception'),
]


class ir_model_export(Model):
    _name = 'ir.model.export'
    _description = 'Export'
    _rec_name = 'create_date'

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
        context used to specify:
         - export_error_management: 'rollback_and_continue' or 'raise' (default='raise', see _generate function)
         - commit_and_new_thread: True/False (default=False)
         if commit_and_new_thread = True, export_error_management is forced to rollback_and_continue
        """
        if isinstance(ids, (int, long)):
            ids = [ids]
        context = context or {}
        commit_and_new_thread = context.get('commit_and_new_thread', False)

        for export_id in ids:
            logger = SmileDBLogger(cr.dbname, 'ir.model.export', export_id, uid)
            if commit_and_new_thread:
                cr.commit()
                t = threading.Thread(target=self._generate_with_new_cursor, args=(cr.dbname, uid, export_id, logger, context))
                t.start()
            else:
                self._generate(cr, uid, export_id, logger, context)
        return True

    def _generate_with_new_cursor(self, dbname, uid, export_id, logger, context):
        try:
            db = pooler.get_db(dbname)
        except Exception:
            return False
        cr = db.cursor()
        context['export_error_management'] = 'rollback_and_continue'
        try:
            self._generate(cr, uid, export_id, logger, context)
            cr.commit()
        except Exception:
            cr.rollback()
        finally:
            cr.close()
        return

    def _generate(self, cr, uid, export_id, logger, context=None):
        """
        Call export method and action
        Catch and log exceptions
        context used to specify:
         - export_error_management: 'rollback_and_continue' or 'raise' (default='raise')
         """
        assert isinstance(export_id, (int, long)), 'ir.model.export, _generate: export_id is supposed to be an integer'

        context = context and context.copy() or {}
        export = self.browse(cr, uid, export_id, context)
        context['logger'] = logger
        context['export_id'] = export.id

        error_management = context.get('export_error_management', 'raise')

        cr.execute('SAVEPOINT smile_export')
        try:
            if export.line_ids or export.export_tmpl_id.force_execute_action:
                res_ids = [line.res_id for line in export.line_ids]
                logger.info('Export start')
                self._run_actions(cr, uid, export, res_ids, context)
                logger.time_info('Export done')
        except Exception, e:
            logger.critical("Export failed: %s" % (_get_exception_message(e),))
            if error_management == 'rollback_and_continue':
                cr.execute("ROLLBACK TO SAVEPOINT smile_export")
                logger.info("Export rollbacking")
                return self.write(cr, uid, export_id, {'state': 'exception',
                                                       'exception': _get_exception_message(e), }, context)
            else:  # export_error_management = raise
                raise e

        try:
            return self.write(cr, uid, export_id, {'state': 'done'}, context)
        except Exception, e:
            logger.error("Could not mark export %s as done: %s" % (export_id, _get_exception_message(e)))
            raise e


class ir_model_export_line(Model):
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
            except Exception:
                name_get_result = [(res_id, "name_get error") for res_id in res_ids]
            for res_id, name in name_get_result:
                buf_result[(res_id, model)] = name

        result = {}
        for line_id in line_id_to_res_id_model:
            result[line_id] = buf_result[line_id_to_res_id_model[line_id]]
        return result

    _columns = {
        'export_id': fields.many2one('ir.model.export', 'Export', required=True, ondelete='cascade'),
        'model': fields.related('export_id', 'model', type='char', size=128, string='Model', readonly=True, store=True),
        'sum': fields.integer('Sum'),
        'res_id': fields.integer('Resource ID', required=True),
        'res_label': fields.function(_get_resource_label, method=True, type='char', size=256, string="Resource label"),
    }

    _order = 'export_id desc'

    _defaults = {
        'sum': 1,
    }
