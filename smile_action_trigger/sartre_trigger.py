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

from datetime import datetime
from dateutil.relativedelta import relativedelta
import inspect
import re
import time
import threading

from openerp import pooler, SUPERUSER_ID, tools
from openerp.modules.registry import Registry
from openerp.osv import fields, orm
from openerp.tools.translate import _

from openerp.addons.smile_log.db_handler import SmileDBLogger

from sartre_decorator import cache_restarter, sartre_decorator
from sartre_tools import _get_browse_record_dict, _get_exception_message, _get_id_from_browse_record


class SartreTrigger(orm.Model):
    _name = 'sartre.trigger'
    _description = 'Action Trigger'
    _decorated_methods = {}

    def _get_trigger_date_type(self, cr, uid, ids, name, args, context=None):
        res = {}
        if isinstance(ids, (int, long)):
            ids = [ids]
        for trigger in self.browse(cr, uid, ids, context):
            if trigger.on_date_type_display1 == 'other_date':
                res[trigger.id] = trigger.on_date_type_display2_id.name
            else:
                res[trigger.id] = trigger.on_date_type_display1
        return res

    def onchange_model_id(self, cr, uid, ids, model_id, on_function, on_other, context=None):
        """Dynamic domain for the field on_function_field_id"""
        res = {'value': {}}
        if model_id:
            model = self.pool.get('ir.model').read(cr, uid, model_id, ['model'])['model']
            obj = self.pool.get(model)
            if on_function:
                function_fields = [field for field in obj._columns
                                   if isinstance(obj._columns[field], (fields.function, fields.related, fields.property))]
                res['domain'] = {'on_function_field_id': "[('model_id', '=', %s),('name', 'in', %s)]" % (model_id, function_fields)}
            if on_other:
                method_names = [attr for attr in dir(obj) if inspect.ismethod(getattr(obj, attr))]
                model_methods_obj = self.pool.get('ir.model.methods')
                model_methods_ids = model_methods_obj.search(cr, uid, [('model_id', '=', model_id), ('name', 'in', method_names)])
                existing_method_names = ['create', 'write', 'unlink']
                existing_method_names += [method['name'] for method in model_methods_obj.read(cr, uid, model_methods_ids, ['name'])]
                for method in method_names:
                    method_args = inspect.getargspec(getattr(obj, method))[0]
                    if method not in existing_method_names and not method.startswith('__') and ('ids' in method_args or 'id' in method_args):
                        model_methods_obj.create(cr, uid, {'name': method, 'model_id': model_id})
        return res

    def _get_logs(self, cr, uid, ids, name, args, context=None):
        res = {}
        for trigger_id in ids:
            res[trigger_id] = self.pool.get('smile.log').search(cr, uid, [
                ('model_name', '=', 'sartre.trigger'), ('res_id', '=', trigger_id),
            ], context=context)
        return res

    def _is_dynamic_field(self, filter_field, model_obj):
        if filter_field:
            # Old values
            if filter_field.startswith('OLD_'):
                return True
            # Function field without fnct_search and not stored
            obj = model_obj
            for field in filter_field.split('.'):
                if field in obj._columns:
                    item_field = obj._columns[field]
                    if isinstance(item_field, fields.function):
                        if not item_field._fnct_search and not item_field.store:
                            return True
                    obj = self.pool.get(item_field._obj)
        return False

    def _is_dynamic_filter(self, cr, uid, item, model_obj, context=None):
        if isinstance(item, tuple) and model_obj:
            # First element
            if self._is_dynamic_field(item[0], model_obj):
                return True
            # Python operator
            operator = self.pool.get('sartre.operator')._get_operator(cr, uid, item[1])
            if operator and operator[0] and operator[0].native_operator == 'none':
                return True
            # Dynamic comparison value
            if re.match('(\[\[.+?\]\])', str(item[2]) or ''):
                return True
        return False

    def _is_python_domain(self, cr, uid, ids, name, args, context=None):
        if isinstance(ids, (int, long)):
            ids = [ids]
        res = {}.fromkeys(ids, False)
        for trigger in self.browse(cr, uid, ids, context):
            model_obj = self.pool.get(trigger.model_id.model)
            if not model_obj:
                continue
            if trigger.on_date and trigger.on_date_type_display1 == 'other_date':
                #other date is function field without fnct_search and not stored
                if self._is_dynamic_field(trigger.on_date_type, model_obj):
                    res[trigger.id] = True
                    continue
            domain = eval(trigger.domain_force or '[]')
            if not domain:
                for filter_ in trigger.filter_ids:
                    domain.extend(eval(filter_.domain or '[]'))
            for item in domain:
                if self._is_dynamic_filter(cr, uid, item, model_obj, context):
                    res[trigger.id] = True
                    break
        return res

    def _get_trigger_ids_from_filters(self, cr, uid, ids, context=None):
        if isinstance(ids, (int, long)):
            ids = [ids]
        return list(set([filter_['trigger_id'][0] for filter_ in self.read(cr, uid, ids, ['trigger_id'], context)]))

    def _get_trigger_ids_from_operators(self, cr, uid, ids, context=None):
        return self.pool.get('sartre.trigger').search(cr, uid, [], context={'active_test': False})

    def _dummy(self, cr, uid, ids, name, arg, context=None):
        return {}.fromkeys(isinstance(ids, (int, long)) and [ids] or ids, '')

    def _search_pid(self, cr, uid, obj, name, domain, context=None):
        trigger_ids = []
        if domain and isinstance(domain[0], tuple):
            value = domain[0][2]
            try:
                value = int(value)
            except ValueError:
                raise orm.except_orm(_('Error !'), _('Pid search field: please enter an integer'))
            log_obj = self.pool.get('smile.log')
            log_ids = log_obj.search(cr, uid, [('pid', '=', value), ('model_name', '=', 'sartre.trigger')], context=context)
            trigger_ids = [log['res_id'] for log in log_obj.read(cr, uid, log_ids, ['res_id'], context)]
        return [('id', 'in', trigger_ids)]

    _columns = {
        'name': fields.char("Name", size=64, required=True),
        'model_id': fields.many2one('ir.model', 'Object', domain=[('osv_memory', '=', False)], required=True, ondelete='cascade'),
        'model': fields.related('model_id', 'model', type='char', string="Model"),
        'active': fields.boolean("Active"),
        'on_create': fields.boolean("Creation"),
        'on_write': fields.boolean("Update"),
        'on_unlink': fields.boolean("Deletion"),
        'on_function': fields.boolean("Function Field"),
        'on_function_type': fields.selection([('set', 'Manually'), ('get', 'Automatically'), ('both', 'Both')], "updated", size=16),
        'on_function_field_id': fields.many2one('ir.model.fields', "Function field", domain="[('model_id', '=', model_id)]",
                                                help="Function, related or property field"),
        'on_other': fields.boolean("Other method", help="Only methods with an argument 'id' or 'ids' in their signatures"),
        'on_other_method_id': fields.many2one('ir.model.methods', "Object method", domain="[('model_id', '=', model_id)]"),
        'on_other_method': fields.related('on_other_method_id', 'name', type='char', string='Method'),
        'on_client_action': fields.boolean("Client Action"),
        'on_client_action_id': fields.many2one('ir.values', "Client Action"),
        'on_client_action_type': fields.selection([('client_print_multi', 'Report'), ('client_action_multi', 'Action'),
                                                   ('client_action_relate', 'Link')], "Type"),
        'on_date': fields.boolean("Date"),
        'on_date_type': fields.function(_get_trigger_date_type, method=True, type='char', size=64, string='Trigger Date Type', store=True),
        'on_date_type_display1': fields.selection([('create_date', 'Creation Date'), ('write_date', 'Update Date'),
                                                   ('other_date', 'Other Date')], 'Trigger Date Type 1', size=16),
        'on_date_type_display2_id': fields.many2one('ir.model.fields', 'Trigger Date Type 2',
                                                    domain="[('ttype','in',['date','datetime']),('model_id','=',model_id)]"),
        'on_date_range': fields.integer('Delay'),
        'on_date_range_type': fields.selection([('minutes', 'Minutes'), ('hours', 'Hours'), ('work_days', 'Work Days'),
                                                ('days', 'Days'), ('weeks', 'Weeks'), ('months', 'Months')], 'Delay Type'),
        'on_date_range_operand': fields.selection([('after', 'After'), ('before', 'Before')], 'Delay Operand'),
        'interval_number': fields.integer('Interval Number'),
        'interval_type': fields.selection([('minutes', 'Minutes'), ('hours', 'Hours'), ('work_days', 'Work Days'),
                                           ('days', 'Days'), ('weeks', 'Weeks'), ('months', 'Months')], 'Interval Unit'),
        'nextcall': fields.datetime("Next Call"),
        'filter_ids': fields.one2many('sartre.filter', 'trigger_id', "Filters", help="The trigger is satisfied if all filters are True"),
        'domain_force': fields.char('Force Domain', size=256, help="Warning: using a Force domain makes all other filters useless"),
        'action_ids': fields.many2many('ir.actions.server', 'sartre_trigger_server_action_rel', 'trigger_id', 'action_id', "Actions"),
        'force_actions_execution': fields.boolean('Force actions execution when resources list is empty'),
        'executions_max_number': fields.integer('Max executions', help="Number of time actions are runned, "
                                                "indicates that actions will always be executed"),
        'log_ids': fields.function(_get_logs, method=True, type='one2many', relation='smile.log', string="Logs"),
        'test_mode': fields.boolean('Test Mode'),
        'exception_handling': fields.selection([('continue', 'Ignore actions in exception'),
                                                ('rollback', 'Rollback transaction')], 'Exception Handling', required=True),
        'exception_warning': fields.selection([('custom', 'Custom'), ('native', 'Native'), ('none', 'None')], 'Exception Warning', required=True),
        'exception_message': fields.char('Exception Message', size=256, translate=True, required=True),
        'python_domain': fields.function(_is_python_domain, method=True, type='boolean', string='Python domain', store={
            'sartre.trigger': (lambda self, cr, uid, ids, context=None: ids, ['domain_force', 'filter_ids'], 10),
            'sartre.filter': (_get_trigger_ids_from_filters, None, 10),
            'sartre.operator': (_get_trigger_ids_from_operators, None, 10),
        }),
        'pid_search': fields.function(_dummy, fnct_search=_search_pid, method=True, type='char', string='Pid'),
        'category_id': fields.many2one('sartre.category', 'Category'),
    }

    def _get_default_category_id(self, cr, uid, context=None):
        category_id = False
        try:
            dummy, category_id = self.pool.get('ir.model.data').get_object_reference(cr, uid, 'smile_action_trigger', 'sartre_category_default0')
        except Exception:
            pass
        return category_id

    _defaults = {
        'active': True,
        'on_function_type': 'both',
        'on_client_action_type': 'client_action_multi',
        'on_date_type_display1': 'create_date',
        'on_date_range': 2,
        'on_date_range_type': 'days',
        'on_date_range_operand': 'after',
        'interval_number': 1,
        'interval_type': 'hours',
        'nextcall': lambda *a: time.strftime("%Y-%m-%d %H:%M:%S"),
        'exception_handling': 'continue',
        'exception_warning': 'custom',
        'exception_message': 'Action failed. Please, contact your administrator.',
        'category_id': _get_default_category_id,
    }

    def create_client_action(self, cr, uid, ids, context=None):
        if isinstance(ids, (int, long)):
            ids = [ids]
        for trigger in self.browse(cr, uid, ids, context):
            if not trigger.on_client_action_id:
                vals = {
                    'name': trigger.name,
                    'model_id': trigger.model_id.id,
                    'state': 'code',
                    'code': "self.pool.get('sartre.trigger').run_now(cr, uid, %d, context)" % (trigger.id,),
                }
                server_action_id = self.pool.get('ir.actions.server').create(cr, uid, vals, context)
                vals2 = {
                    'name': trigger.name,
                    'object': True,
                    'model_id': trigger.model_id.id,
                    'model': trigger.model,
                    'key2': trigger.on_client_action_type,
                    'value': 'ir.actions.server,%d' % server_action_id,
                }
                client_action_id = self.pool.get('ir.values').create(cr, uid, vals2, context)
                trigger.write({'on_client_action_id': client_action_id})
        return True

    @tools.cache(skiparg=3)
    def get_trigger_ids(self, cr, uid, model, method):
        domain = [('model', '=', model)]
        if method in ['create', 'write', 'unlink', 'function']:
            domain.append(('on_' + method, '=', True))
        else:
            domain.append(('on_other_method', '=', method))
        return self.search(cr, uid, domain, context={'active_test': True})

    @tools.cache(skiparg=3)
    def get_fields_to_save_old_values(self, cr, uid, ids):
        res = []
        if isinstance(id, (int, long)):
            ids = [ids]
        for trigger in self.browse(cr, uid, ids, context={'active_test': True}):
            for method in ['write', 'unlink', 'function', 'other']:
                if getattr(trigger, 'on_' + method):
                    for filter_ in trigger.filter_ids:
                        domain = eval(filter_.domain)
                        if isinstance(domain, list):
                            for condition in domain:
                                if condition[0].startswith('OLD_'):
                                    res.append(condition[0].replace('OLD_', '').split('.')[0])
        return list(set(res))

    def _decorate_trigger_method(self, method):
        method_name = method.__name__
        if method_name == 'trigger_method':
            return
        object_class = method.im_class
        object_name = getattr(object_class, '_name', None) or object_class.__name__
        if method_name in self._decorated_methods.get(object_name, {}):
            original_class = self._decorated_methods[object_name][method_name]['original_class']
            original_method = self._decorated_methods[object_name][method_name]['original_method']
            setattr(original_class, method_name, original_method)
        self._decorated_methods.setdefault(object_name, {})[method_name] = {'original_class': object_class, 'original_method': method}
        setattr(object_class, method_name, sartre_decorator(method))

    def decorate_trigger_methods(self, cr):
        methods_to_decorate = []
        trigger_ids = self.search(cr, 1, [], context={'active_test': True})
        for trigger in self.browse(cr, 1, trigger_ids):
            for orm_method in ('create', 'write', 'unlink'):
                if getattr(trigger, 'on_%s' % orm_method):
                    methods_to_decorate.append(getattr(orm.Model, orm_method))
            if trigger.on_function:
                for field_method in ('get', 'set'):
                    if trigger.on_function_type in (field_method, 'both'):
                        methods_to_decorate.append(getattr(fields.function, field_method))
            if trigger.on_other:
                class_obj = self.pool.get(trigger.model_id.model)
                if not class_obj:
                    continue
                m_class = class_obj.__class__
                m_name = trigger.on_other_method
                if m_name and hasattr(m_class, m_name):
                    methods_to_decorate.append(getattr(m_class, m_name))
        methods_to_decorate = list(set(methods_to_decorate))
        for method in methods_to_decorate:
            self._decorate_trigger_method(method)
        return True

    def cache_restart(self, cr):
        self.get_trigger_ids.clear_cache(self)
        self.get_fields_to_save_old_values.clear_cache(self)
        self.decorate_trigger_methods(cr)
        return True

    def __init__(self, pool, cr):
        super(SartreTrigger, self).__init__(pool, cr)
        cr.execute("SELECT relname FROM pg_class WHERE relname=%s", (self._table,))
        if cr.fetchall():
            columns = [column for column in self._columns if not self._columns[column]._type.endswith('2many') and
                       (not isinstance(self._columns[column], (fields.function, fields.property, fields.related)) or
                        self._columns[column].store)]
            cr.execute("SELECT attname FROM pg_attribute WHERE attrelid = (SELECT oid FROM pg_class WHERE relname=%s) AND attname IN %s",
                       (self._table, tuple(columns)))
            res = cr.fetchall()
            if res and len(res) == len(columns):
                self.decorate_trigger_methods(cr)
        setattr(Registry, 'load', cache_restarter(getattr(Registry, 'load')))

    def create(self, cr, uid, vals, context=None):
        trigger_id = super(SartreTrigger, self).create(cr, uid, vals, context)
        self.cache_restart(cr)
        return trigger_id

    def write(self, cr, uid, ids, vals, context=None):
        res = super(SartreTrigger, self).write(cr, uid, ids, vals, context)
        self.cache_restart(cr)
        return res

    def unlink(self, cr, uid, ids, context=None):
        res = super(SartreTrigger, self).unlink(cr, uid, ids, context)
        self.cache_restart(cr)
        return res

    def _add_trigger_date_filter(self, cr, uid, trigger, context):
        """Build trigger date filter"""
        if trigger.on_date:
            datetime_format = '%Y-%m-%d %H:%M:%S'
            now = datetime.now()
            interval_number = trigger.on_date_range
            interval_type = str(trigger.on_date_range_type)
            interval_operand = trigger.on_date_range_operand
            # Update trigger next call
            try:
                nextcall = datetime.strptime(trigger.nextcall, datetime_format)
            except ValueError:  # To be compatible with the old version of this module
                nextcall = datetime.strptime(trigger.nextcall, datetime_format + '.%f')
            while nextcall <= now:
                nextcall += relativedelta(**{str(trigger.interval_type): trigger.interval_number})
            self.write(cr, 1, trigger.id, {'nextcall': nextcall.strftime(datetime_format)}, context)
            # Add datetime filter
            field = trigger.on_date_type
            limit_date = now
            if interval_operand == 'after':
                limit_date -= relativedelta(**{interval_type: interval_number})
            if interval_operand == 'before':
                limit_date += relativedelta(**{interval_type: interval_number})
            return (field, '<=', limit_date.strftime(datetime_format))
        return

    def _add_max_executions_filter(self, cr, uid, trigger, context):
        """Build max executions filter"""
        if trigger.executions_max_number:
            cr.execute("SELECT res_id FROM sartre_execution WHERE trigger_id=%s AND executions_number>=%s",
                       (trigger.id, trigger.executions_max_number))
            res_ids_off = cr.fetchall()
            if context.get('active_object_ids'):
                res_ids = list(set(context.get('active_object_ids', [])) - set([item[0] for item in res_ids_off]))
                return ('id', 'in', res_ids)
            else:
                return ('id', 'not in', [item[0] for item in res_ids_off])
        return

    def _build_python_domain(self, cr, uid, trigger, domain, context):
        """Updated filters based on old or dynamic values, or Python operators"""
        domain = domain or []
        operator_obj = self.pool.get('sartre.operator')
        old_values = context.get('old_values', {})
        arg_values = context.get('arg_values', {})
        model_obj = self.pool.get(trigger.model_id.model)
        if 'active_object_ids' in context:
            all_active_object_ids = context['active_object_ids']
        else:
            all_active_object_ids = model_obj.search(cr, uid, [], context=context)
        fields_list = self.get_fields_to_save_old_values(cr, SUPERUSER_ID, [trigger.id])
        current_values = _get_browse_record_dict(model_obj, cr, uid, all_active_object_ids, fields_list, context=context)
        for index, condition in enumerate(domain):
            if self._is_dynamic_filter(cr, uid, condition, model_obj, context):
                active_object_ids = all_active_object_ids[:]

                field, operator_symbol, other_value = condition
                fields_list = field.replace('OLD_', '').split('.')
                field, remote_field = fields_list[0], len(fields_list) > 1 and '.'.join(fields_list[1:]) or ''
                try:
                    operator_inst, opposite_operator = operator_obj._get_operator(cr, uid, operator_symbol)
                except Exception:
                    raise orm.except_orm(_('Warning!'), _("The operator %s doesn't exist!") % operator_symbol)
                dynamic_other_value = other_value and re.match('(\[\[.+?\]\])', str(other_value))
                for object_ in self.pool.get(trigger.model_id.model).browse(cr, uid, active_object_ids, context):
                    if dynamic_other_value:
                        other_value = _get_id_from_browse_record(eval(str(dynamic_other_value.group()[2:-2]).strip(), {
                            'uid': uid,
                            'object': object_,
                            'context': context,
                            'time': time,
                            'relativedelta': relativedelta,
                        }))
                    current_field_value = current_values.get(object_.id, {}).get(field)
                    old_field_value = old_values.get(object_.id, {}).get(field)
                    arg_value = arg_values.get(field)
                    if remote_field:
                        current_field_value = _get_id_from_browse_record(getattr(current_field_value, remote_field))
                        old_field_value = _get_id_from_browse_record(old_field_value and getattr(old_field_value, remote_field))
                    localdict = {'selected_field_value': 'OLD_' in condition[0] and old_field_value or current_field_value,
                                 'current_field_value': current_field_value,
                                 'old_field_value': old_field_value,
                                 'other_value': other_value,
                                 'arg_value': arg_value}
                    if operator_inst:
                        exec operator_inst.expression in localdict
                    if bool(opposite_operator) == bool(localdict.get('result', opposite_operator)):
                        active_object_ids.remove(object_.id)
                domain[index] = ('id', 'in', active_object_ids)
        return domain

    def _build_domain_expression(self, cr, uid, trigger, context):
        """Build domain expression"""
        # Define domain from domain_force
        domain = trigger.domain_force and eval(trigger.domain_force.replace('%today', time.strftime('%Y-%m-%d %H:%M:%S'))) or []
        # Add filters one by one if domain_force is empty
        if not domain:
            for filter_ in trigger.filter_ids:
                domain.extend(eval(filter_.domain.replace('%today', time.strftime('%Y-%m-%d %H:%M:%S'))))
        # Add general filters
        for filter_name in ('_add_trigger_date_filter', '_add_max_executions_filter'):
            domain_extension = getattr(self, filter_name)(cr, uid, trigger, context)
            if domain_extension:
                domain.append(domain_extension)
        # Update filters based on old or dynamic values or Python operators
        if trigger.python_domain:
            domain = self._build_python_domain(cr, uid, trigger, domain, context)
        if 'active_object_ids' in context:
            domain.append(('id', 'in', context['active_object_ids']))
        return domain

    def run_now(self, cr, uid, ids, context=None):
        """Execute now server actions"""
        context = context or {}
        context = dict(context)  # Can't use deepcopy because of browse_record_list
        context.setdefault('active_test', False)
        if isinstance(ids, (int, long)):
            ids = [ids]
        for trigger in self.read(cr, uid, ids, ['test_mode'], context):
            context['test_mode'] = trigger['test_mode']
            self._run_now(cr, uid, trigger['id'], context)
        return True

    def _get_filtered_object_ids(self, cr, uid, trigger, context):
        # Build domain expression
        domain = self._build_domain_expression(cr, uid, trigger, context)
        # Search objects which validate trigger filters
        res_ids = self.pool.get(trigger.model_id.model).search(cr, uid, domain, context=context)
        # To avoid infinite recursion
        context.setdefault('triggers', {}).setdefault(trigger.id, [])
        res_ids = list(set(res_ids) - set(context['triggers'][trigger.id]))
        context['triggers'][trigger.id].extend(res_ids)
        return res_ids

    def _run_now(self, cr, uid, trigger_id, context):
        logger = SmileDBLogger(cr.dbname, self._name, trigger_id, uid)

        # Get sequence in order to differentiate logs per run
        context.setdefault('pid_list', []).append(str(logger.pid).rjust(8, '0'))
        pid = '-'.join((str(x) for x in context['pid_list']))
        if not pid:
            logger.critical('Action Trigger failed: impossible to get a pid for dbname %s' % (cr.dbname))
            return

        # Get sequence in order to differentiate logs per run
        if context.get('test_mode', False):
            logger.info('[%s] Trigger in test mode' % (pid,))
        logger.debug('[%s] Trigger on %s' % (pid, context.get('trigger', 'manual')))
        logger.debug('[%s] Context: %s' % (pid, context))
        trigger = self.browse(cr, uid, trigger_id, context)

        # Filter objects
        filtered_object_ids = []
        try:
            filtered_object_ids = self._get_filtered_object_ids(cr, uid, trigger, context)
            logger.debug('[%s] Successful Objects Filtering: %s' % (pid, filtered_object_ids))
        except Exception, e:
            logger.exception('[%s] Objects Filtering failed: %s' % (pid, _get_exception_message(e)))
            if trigger.exception_handling == 'continue' or trigger.exception_warning == 'none':
                return True
            else:
                cr.rollback()
                logger.time_info("[%s] Transaction rolled back" % (pid,))
                if trigger.exception_warning == 'custom':
                    raise orm.except_orm(_('Error'), _('%s\n[Pid: %s]') % (trigger.exception_message, pid))
                elif trigger.exception_warning == 'native':
                    raise orm.except_orm(_('Error'), _('%s\n[Pid: %s]') % (_get_exception_message(e), pid))
        # Execute server actions for filtered objects
        if filtered_object_ids or trigger.force_actions_execution:
            logger.info('[%s] Trigger on %s for objects %s,%s' % (pid, context.get('trigger', 'manual'), trigger.model_id.model, filtered_object_ids))
            if context.get('test_mode', False):
                cr.execute("SAVEPOINT smile_action_trigger_test_mode_%s", (trigger.id,))
            for action in trigger.action_ids:
                if action.active:
                    if trigger.exception_handling == 'continue':
                        cr.execute("SAVEPOINT smile_action_trigger_%s", (trigger.id,))
                    try:
                        logger.debug('[%s] Launch Action: %s - Objects: %s,%s' % (pid, action.name, action.model_id.model, filtered_object_ids))
                        self._run_action(cr, uid, action, filtered_object_ids, context, logger, pid)
                        if not action.specific_thread:
                            logger.time_info('[%s] Successful Action: %s - Objects: %s,%s'
                                             % (pid, action.name, action.model_id.model, filtered_object_ids))
                        else:
                            logger.info('[%s] Action launched in a new thread: %s - Objects: %s,%s'
                                        % (pid, action.name, action.model_id.model, filtered_object_ids))
                    except Exception, e:
                        logger.exception('[%s] Action failed: %s - %s' % (pid, action.name, _get_exception_message(e)))
                        if trigger.exception_handling == 'continue' and not action.force_rollback:
                            cr.execute("ROLLBACK TO SAVEPOINT smile_action_trigger_%s", (trigger.id,))
                        else:
                            cr.rollback()
                            logger.time_info("[%s] Transaction rolled back" % (pid,))
                            if trigger.exception_warning == 'custom':
                                raise orm.except_orm(_('Error'), _('%s\n[Pid: %s]') % (trigger.exception_message, pid))
                            elif trigger.exception_warning == 'native':
                                raise orm.except_orm(_('Error'), _('%s\n[Pid: %s]') % (_get_exception_message(e), pid))
                            else:  # elif trigger.exception_warning == 'none':
                                return True
            if context.get('test_mode', False):
                cr.execute("ROLLBACK TO SAVEPOINT smile_action_trigger_test_mode_%s", (trigger.id,))
                logger.time_info("[%s] Actions execution rolled back" % (pid,))
            if trigger.executions_max_number:
                for object_id in filtered_object_ids:
                    self.pool.get('sartre.execution').update_executions_counter(cr, uid, trigger, object_id)
        logger.time_debug('[%s] End' % (pid,))
        return True

    def _run_action(self, cr, uid, action, object_ids, context, logger, pid):
        if action.specific_thread:
            new_thread = threading.Thread(target=self._run_action_in_new_thread, args=(cr.dbname, uid, action, object_ids, context, logger, pid))
            new_thread.start()
        else:
            self._run_action_for_object_ids(cr, uid, action, object_ids, context)
        return True

    def _run_action_in_new_thread(self, dbname, uid, action, object_ids, context, logger, pid):
        try:
            db = pooler.get_db(dbname)
        except Exception:
            return
        cr = db.cursor()
        try:
            self._run_action_for_object_ids(cr, uid, action, object_ids, context)
            cr.commit()
            logger.time_info('[%s] Successful Action: %s - Objects: %s,%s' % (pid, action.name, action.model_id.model, object_ids))
        except Exception, e:
            logger.exception('[%s] Action failed: %s - %s' % (pid, action.name, _get_exception_message(e)))
        finally:
            cr.close()
        return

    def _run_action_for_object_ids(self, cr, uid, action, object_ids, context):
        context['active_ids'] = self._get_ids_by_group(cr, uid, action, object_ids, context)
        for active_id in context['active_ids']:
            context['launch_by_trigger'] = True
            context['active_id'] = active_id
            context['active_model'] = action.model_id.model
            self.pool.get('ir.actions.server').run(cr, action.user_id and action.user_id.id or uid, [action.id], context=context)
        return True

    def _get_ids_by_group(self, cr, uid, action, object_ids, context):
        if not action.run_once:
            # object_ids passed one by one
            return object_ids
        elif not action.group_by:
            # object_ids passed all together
            return [object_ids]
        else:
            # object_ids grouped by identical 'group_by eval value'
            action_objects = self.pool.get(action.model_id.model).browse(cr, uid, object_ids, context)
            eval_to_ids = {}
            for action_object in action_objects:
                value = eval(action.group_by, {'object': action_object, 'context': context, 'time': time})
                eval_to_ids.setdefault(value, []).append(action_object.id)
            return eval_to_ids.values()

    def check_triggers(self, cr, uid, context=None):
        """Call the scheduler to check date based trigger triggers"""
        # Search triggers to execute
        trigger_ids = self.search(cr, uid, [('active', '=', True), ('on_date', '=', True), ('nextcall', '<=', time.strftime("%Y-%m-%d %H:%M:%S"))])
        if trigger_ids:
            # Launch triggers execution
            context = context or {}
            context['trigger'] = 'date'
            self.run_now(cr, uid, trigger_ids, context)
        return True

    def check_method_based_triggers(self, obj, cr, uid, method, field_name=None, calculation_method=None):
        """Check method based trigger triggers"""
        field_name = field_name or []
        if not isinstance(field_name, (list, tuple)):
            field_name = [field_name]
        trigger_ids = []
        trigger_obj = hasattr(self, 'pool') and self.pool.get('sartre.trigger') or pooler.get_pool(cr.dbname).get('sartre.trigger')
        if trigger_obj:
            # Search triggers to execute
            trigger_ids = list(trigger_obj.get_trigger_ids(cr, 1, obj._name, method))
            if trigger_ids and method == 'function':
                for trigger_id in list(trigger_ids):
                    trigger = trigger_obj.browse(cr, uid, trigger_id)
                    if not isinstance(field_name, (list, tuple)):
                        field_name = [field_name]
                    if trigger.on_function_field_id.name not in field_name or trigger.on_function_type not in [calculation_method, 'both']:
                        trigger_ids.remove(trigger_id)
        return trigger_ids
