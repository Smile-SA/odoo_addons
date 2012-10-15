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

import inspect
import re
import time
import threading

from datetime import datetime
from dateutil.relativedelta import relativedelta

from modules.registry import Registry

from osv import fields, orm, osv
import pooler
import tools
from tools.func import wraps
from tools.translate import _

from smile_log.db_handler import SmileDBLogger


def _get_exception_message(exception):
    msg = isinstance(exception, (osv.except_osv, orm.except_orm)) and exception.value or exception
    return tools.ustr(msg)


def _get_browse_record_dict(obj, cr, uid, ids, fields_list=None, context=None):
    """Get a dictionary of dictionary from browse records list"""
    if isinstance(ids, (int, long)):
        ids = [ids]
    if fields_list is None:
        fields_list = [f for f in obj._columns if obj._columns[f]._type != 'binary']
    browse_record_dict = {}
    for object_inst in obj.browse(cr, 1, ids, context):
        for field in fields_list:
            browse_record_dict.setdefault(object_inst.id, {})[field] = getattr(object_inst, field)
    return browse_record_dict


def _get_id_from_browse_record(value):
    if isinstance(value, orm.browse_record):
        value = value.id
    if isinstance(value, orm.browse_record_list):
        value = [v.id for v in value]
    return value


def cache_restarter(original_method):
    @wraps(original_method)
    def wrapper(self, cr, module):
        res = original_method(self, cr, module)
        trigger_obj = self.get('sartre.trigger')
        if trigger_obj and hasattr(trigger_obj, 'cache_restart'):
            cr.execute("SELECT relname FROM pg_class WHERE relname=%s", (trigger_obj._table,))
            if cr.fetchall():
                trigger_obj.cache_restart(cr)
        return res
    return wrapper


def get_original_method(method):
    """Get original method if not already decorated by Sartre"""
    while method.func_closure:
        if method.__name__ == 'trigger_method':
            return
        method = method.func_closure[0].cell_contents
    return method


class IrModelMethods(orm.Model):
    _name = 'ir.model.methods'
    _description = 'Model Method'
    _order = 'name'

    _columns = {
        'name': fields.char('Method name', size=128, select=True, required=True),
        'model_id': fields.many2one('ir.model', 'Object', select=True, required=True, ondelete='cascade'),
    }

    def get_method_args(self, cr, uid, method_id, context=None):
        assert isinstance(method_id, (int, long)), 'method_id must be an integer'
        method = self.browse(cr, uid, method_id, context=context)
        model_class = self.pool.get(method.model_id.model).__class__
        original_method = get_original_method(getattr(model_class, method.name))
        return ', '.join(inspect.getargspec(original_method)[0])


class SartreOperator(orm.Model):
    _name = 'sartre.operator'
    _description = 'Action Trigger Operator'

    _columns = {
        'name': fields.char('Name', size=30, required=True),
        'symbol': fields.char('Symbol', size=8, required=True),
        'opposite_symbol': fields.char('Opposite symbol', size=12, help="Opposite symbol for SQL filter"),
        'value_age_filter': fields.selection([('current', 'Current'), ('old', 'Old'), ('both', 'Both')], 'Value Age Filter', required=True),
        'native_operator': fields.selection([
            ('=', 'is equal to'), ('<=', 'less than'), ('>=', 'greater than'),
            ('like', 'contains (case-sensitive matching)'), ('ilike', 'contains (case-insensitive matching)'),
            ('in', 'in'), ('child_of', 'child of'), ('none', 'none'),
        ], 'Native Operator', required=True),
        'other_value_necessary': fields.boolean('Other Value Necessary'),
        'other_value_transformation': fields.char('Value Transformation', size=64, help="Useful only for native operator"),
        'expression': fields.text('Expression'),
    }

    _defaults = {
        'native_operator': 'none',
        'value_age_filter': 'both',
        'other_value_necessary': False,
    }

    @tools.cache(skiparg=3)
    def _get_operator(self, cr, uid, name):
        operator = opposite_operator = None
        if name.startswith('not '):
            opposite_operator = True
            name = name.replace('not ', '')
        operator_id = self.search(cr, uid, ['|', ('symbol', '=', name), ('opposite_symbol', '=', name)], limit=1)
        if operator_id:
            operator = self.browse(cr, uid, operator_id[0])
            if name == operator.opposite_symbol:
                opposite_operator = not opposite_operator
        return operator, opposite_operator

    def __init__(self, pool, cr):
        super(SartreOperator, self).__init__(pool, cr)
        self.clear_caches()

    def create(self, cr, uid, vals, context=None):
        operator_id = super(SartreOperator, self).create(cr, uid, vals, context)
        self.clear_caches()
        return operator_id

    def write(self, cr, uid, ids, vals, context=None):
        res = super(SartreOperator, self).write(cr, uid, ids, vals, context)
        self.clear_caches()
        return res

    def unlink(self, cr, uid, ids, context=None):
        res = super(SartreOperator, self).unlink(cr, uid, ids, context)
        self.clear_caches()
        return res


class SartreCategory(orm.Model):
    _name = 'sartre.category'
    _description = 'Action Trigger Category'

    _columns = {
        'name': fields.char('Name', size=64, required=True),
    }


class SartreTrigger(orm.Model):
    _name = 'sartre.trigger'
    _description = 'Action Trigger'

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
                    break
            domain = eval(trigger.domain_force or '[]')
            if not domain:
                for filter_ in trigger.filter_ids:
                    domain.extend(eval(filter_.domain or '[]'))
            for item in domain:
                is_dynamic_item = self._is_dynamic_filter(cr, uid, item, model_obj, context)
                if is_dynamic_item:
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
                                    res.append(condition[0].replace('OLD_', ''))
        return list(set(res))

    def decorate_trigger_methods(self, cr):
        methods_to_decorate = []
        trigger_ids = self.search(cr, 1, [], context={'active_test': True})
        for trigger in self.browse(cr, 1, trigger_ids):
            for orm_method in ('create', 'write', 'unlink'):
                if getattr(trigger, 'on_%s' % orm_method):
                    original_method = get_original_method(getattr(orm.Model, orm_method))
                    if original_method:
                        methods_to_decorate.append(original_method)
            if trigger.on_function:
                for field_method in ('get', 'set'):
                    if trigger.on_function_type in (field_method, 'both'):
                        original_method = get_original_method(getattr(fields.function, field_method))
                        if original_method:
                            methods_to_decorate.append(original_method)
            if trigger.on_other:
                class_obj = self.pool.get(trigger.model_id.model)
                if not class_obj:
                    continue
                m_class = class_obj.__class__
                m_name = trigger.on_other_method
                if m_name and hasattr(m_class, m_name):
                    other_method = getattr(m_class, m_name)
                    original_method = get_original_method(other_method)
                    if original_method:
                        methods_to_decorate.append(original_method)
        methods_to_decorate = list(set(methods_to_decorate))
        for unbound_method in methods_to_decorate:
            setattr(unbound_method.im_class, unbound_method.__name__, sartre_decorator(unbound_method))
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
        all_active_object_ids = context.get('active_object_ids', model_obj.search(cr, uid, [], context=context))
        current_values = _get_browse_record_dict(model_obj, cr, uid, all_active_object_ids, context=context)
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
        elif context.get('active_object_ids'):
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


class SartreFilter(orm.Model):
    _name = 'sartre.filter'
    _description = 'Action Trigger Filter'
    _rec_name = 'field_id'

    def onchange_get_domain(self, cr, uid, ids, field='', operator_id=False, opposite=False,
                            value='', value_age='current', value_type='static', context=None):
        """Build domain expression from filter items"""
        res = {}
        operator_pool = self.pool.get('sartre.operator')
        if field and operator_id and (value or not operator_pool.read(cr, uid, operator_id, ['other_value_necessary'])['other_value_necessary']):
            field_name = (value_age == 'old' and 'OLD_' or '') + field
            operator_inst = operator_pool.browse(cr, uid, operator_id)
            symbol = opposite and operator_inst.opposite_symbol or operator_inst.symbol
            if value_age == 'current' and value_type == 'static':
                value = operator_inst.other_value_transformation and eval(operator_inst.other_value_transformation, {'value': value}) or value
            if value_type == 'dynamic' and value:
                value = '[[ object.' + value + ' ]]'
            res['value'] = {'domain': str([(field_name, symbol, value)])}
        return res

    def _build_field_expression(self, cr, uid, field_id, field_expression='', context=None):
        """Build field expression"""
        field_pool = self.pool.get('ir.model.fields')
        field_obj = field_pool.read(cr, uid, field_id, ['name', 'ttype', 'relation', 'model'])
        field_expr = field_expression and (field_expression.split('.')[:-1]
                                           and '.'.join(field_expression.split('.')[:-1])
                                           or field_expression) + '.' or ''
        obj = self.pool.get(field_obj['model'])
        if field_obj['name'] in obj._columns and 'fields.related' in str(obj._columns[field_obj['name']]):
            field_expr += obj._columns[field_obj['name']].arg[0] + '.'
        field_expr += field_obj['name']
        if field_obj['ttype'] in ['many2one', 'one2many', 'many2many']:
            field_expr += field_obj['ttype'] == 'many2one' and '.' or ''
            field_expr += field_obj['ttype'] in ['one2many', 'many2many'] and '[0].' or ''
            field_expr += self.pool.get(field_obj['relation'])._rec_name
        return field_expr

    def _check_field_expression(self, cr, uid, model_id, field_expression='', context=None):
        """Check field expression"""
        field_list = field_expression and (field_expression.split('.')[:-1] or [field_expression])
        if field_list:
            field_pool = self.pool.get('ir.model.fields')
            model = self.pool.get('ir.model').read(cr, uid, model_id, ['model'])['model']
            for f_name in field_list:
                if '[' in f_name:
                    f_name = f_name[: f_name.index('[')]
                f_id = field_pool.search(cr, uid, [('model', '=', model), ('name', '=', f_name)], limit=1, context=context)
                if not f_id:
                    raise orm.except_orm(_('Error'), _("The field %s is not in the model %s !" % (f_name, model)))
                f_obj = field_pool.read(cr, uid, f_id[0], ['name', 'ttype', 'relation'])
                if f_obj['ttype'] in ['many2one', 'one2many', 'many2many']:
                    model = f_obj['relation']
                    model_id = self.pool.get('ir.model').search(cr, uid, [('model', '=', model)], limit=1, context=context)[0]
                elif len(field_expression.split('.')) > 1:
                    raise orm.except_orm(_('Error'), _("The field %s is not a relation field !" % f_obj['name']))
        return model_id

    def onchange_get_field_domain(self, cr, uid, ids, model_id, field_expression='', context=None):
        """Get field domain"""
        model_id = self._check_field_expression(cr, uid, model_id, field_expression, context)
        return {'value': {'field_id': False}, 'domain': {'field_id': "[('model_id', '=', %d)]" % model_id}}

    def onchange_get_field_expression(self, cr, uid, ids, model_id, field_expression='', field_id=False, context=None):
        """Update the field expression"""
        if field_id:
            field_expression = self._build_field_expression(cr, uid, field_id, field_expression, context)
        res = self.onchange_get_field_domain(cr, uid, ids, model_id, field_expression, context)
        res.setdefault('value', {}).update({'field_expression': field_expression})
        return res

    def onchange_get_value_age_domain(self, cr, uid, ids, field='', operator_id=False,
                                      opposite=False, value='', value_age='current', value_type='static', context=None):
        """Update the field 'value_age'"""
        value_age_filter = operator_id and self.pool.get('sartre.operator').read(cr, uid, operator_id, ['value_age_filter'])['value_age_filter']
        if value_age_filter != 'both':
            value_age = value_age_filter
        res = self.onchange_get_domain(cr, uid, ids, field, operator_id, opposite, value, value_age, value_type, context)
        res.setdefault('value', {})
        res['value'] = {'value_age': value_age, 'value_age_readonly': value_age_filter != 'both'}
        return res

    _columns = {
        "trigger_id": fields.many2one('sartre.trigger', "Trigger", required=True, ondelete='cascade'),
        "field_name": fields.char("Field", size=256),
        "value_age": fields.selection([
            ('current', 'Current Value'),
            ('old', 'Old Value'),
        ], "Value Age", select=True),
        "value_age_readonly": fields.boolean("Value Age Readonly"),
        "operator_id": fields.many2one('sartre.operator', "Operator"),
        "opposite": fields.boolean('Opposite'),
        "value": fields.char("Value", size=128, help="Dynamic value corresponds to an object field"),
        "value_type": fields.selection([('static', 'Static'), ('dynamic', 'Dynamic')], "Value Type"),
        "domain": fields.char("Domain", size=256, required=True),
        "field_id": fields.many2one('ir.model.fields', "Field Builder"),
        "field_expression": fields.char("Expression to copy", size=256),
    }

    _defaults = {
        'value_age': 'current',
        'value_type': 'static',
    }


class SartreExecution(orm.Model):
    _name = 'sartre.execution'
    _description = 'Action Trigger Execution'
    _rec_name = 'trigger_id'

    _columns = {
        'trigger_id': fields.many2one('sartre.trigger', 'Trigger', required=False, select=True, ondelete='cascade'),
        'model_id': fields.many2one('ir.model', 'Object', required=False, select=True),
        'res_id': fields.integer('Resource', required=False),
        'executions_number': fields.integer('Executions'),
    }

    def update_executions_counter(self, cr, uid, trigger, res_id):
        """Update executions counter"""
        if not (trigger and res_id):
            raise orm.except_orm(_('Error'), _('Action Trigger Execution: all arguments are mandatory !'))
        log_id = self.search(cr, uid, [('trigger_id', '=', trigger.id), ('model_id', '=', trigger.model_id.id), ('res_id', '=', res_id)], limit=1)
        if log_id:
            executions_number = self.read(cr, uid, log_id[0], ['executions_number'])['executions_number'] + 1
            return self.write(cr, uid, log_id[0], {'executions_number': executions_number})
        else:
            return self.create(cr, uid, {'trigger_id': trigger.id, 'model_id': trigger.model_id.id,
                                         'res_id': res_id, 'executions_number': 1}) and True


def _get_args(method, args, kwargs):
    args_names = inspect.getargspec(method)[0]
    args_dict = {}.fromkeys(args_names, False)
    for index, arg in enumerate(args_names):
        if index < len(args):
            args_dict[arg] = args[index]
    obj = args_dict.get('obj') or args_dict.get('self', False)
    cr = args_dict.get('cursor') or args_dict.get('cr', False)
    uid = args_dict.get('uid') or args_dict.get('user', False)
    ids = args_dict.get('ids') or args_dict.get('id', [])
    vals = args_dict.get('values') or args_dict.get('vals', {})
    if isinstance(ids, (int, long)):
        ids = [ids]
    field_name = args_dict.get('name', '')
    context = isinstance(args_dict.get('context'), dict) and dict(args_dict['context']) or {}
    return obj, cr, uid, ids, field_name, vals, context


def sartre_decorator(original_method):
    def trigger_method(*args, **kwargs):
        # Get arguments
        obj, cr, uid, ids, field_name, vals, context = _get_args(original_method, args, kwargs)
        method_name = original_method.__name__
        context['trigger'] = method_name
        trigger_obj = obj.pool.get('sartre.trigger')
        trigger_ids = []
        if trigger_obj:
            # Case: trigger on function
            calculation_method = False
            if method_name in ('get', 'set') and original_method.im_class == fields.function:
                calculation_method = method_name
                method_name = 'function'
            # Search triggers
            trigger_ids = trigger_obj.check_method_based_triggers(obj, cr, uid, method_name, field_name, calculation_method)
            # Save old values if triggers exist
            if trigger_ids:
                fields_list = trigger_obj.get_fields_to_save_old_values(cr, 1, trigger_ids)
                context.update({
                    'active_object_ids': ids,
                    'old_values': _get_browse_record_dict(obj, cr, uid, ids, fields_list, context),
                    'arg_values': vals,
                })
                # Case: trigger on unlink
                if method_name == 'unlink':
                    trigger_obj.run_now(cr, uid, trigger_ids, context=context)
        # Execute original method
        result = original_method(*args, **kwargs)
        # Run triggers if exists
        if trigger_obj and trigger_ids and method_name != 'unlink':
            # Case: trigger on create
            if method_name == 'create':
                context['active_object_ids'] = [result]
            trigger_obj.run_now(cr, uid, trigger_ids, context=context)
        return result
    return trigger_method


def sartre_validate(self, cr, uid, ids, context=None):
    context = context or {}
    lng = context.get('lang', False) or 'en_US'
    trans = self.pool.get('ir.translation')
    error_msgs = []
    for constraint in self._constraints:
        fun, msg, fields_list = constraint
        args = (self, cr, uid, ids)
        kwargs = {}
        if 'context' in inspect.getargspec(fun)[0]:
            kwargs = {'context': context}
        if not fun(*args, **kwargs):
            if hasattr(msg, '__call__'):
                tmp_msg = msg(self, cr, uid, ids, context=context)
                if isinstance(tmp_msg, tuple):
                    tmp_msg, params = tmp_msg
                    translated_msg = tmp_msg % params
                else:
                    translated_msg = tmp_msg
            else:
                translated_msg = trans._get_source(cr, uid, self._name, 'constraint', lng, msg) or msg
            fields_list = fields_list or []
            error_msgs.append(
                _("Error occurred while validating the field(s) %s: %s") % (','.join(fields_list), translated_msg)
            )
            self._invalids.update(fields_list)
    if error_msgs:
        # Added by smile #
        if not context.get('pid_list'):
            cr.rollback()
        ##################
        raise orm.except_orm('ValidateError', '\n'.join(error_msgs))
    else:
        self._invalids.clear()

orm.BaseModel._validate = sartre_validate
