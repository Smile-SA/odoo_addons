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

from osv import fields, osv, orm
import service
import netsvc
import pooler
import re
import time
from mx.DateTime import RelativeDateTime, now
import tools
from tools.translate import _
import traceback
import inspect
import operator

def _get_browse_record_dict(self, cr, uid, ids):
    """Get a dictionary of dictionary from browse records list"""
    if isinstance(ids, (int, long)):
        ids = [ids]
    return dict([(object.id, dict([(field, eval('obj.' + field, {'obj':object})) for field in self._columns])) for object in self.browse(cr, uid, ids)])

class ir_model_methods(osv.osv):
    _name = 'ir.model.methods'

    _columns = {
        'name': fields.char('Method name', size=128, select=True, required=True),
        'model_id': fields.many2one('ir.model', 'Object', select=True, required=True),
    }
ir_model_methods()

class sartre_operator(osv.osv):
    _name = 'sartre.operator'
    _description = 'Sartre Operator'

    def __init__(self, pool, cr):
        super(sartre_operator, self).__init__(pool, cr)
        cr.execute("SELECT * FROM pg_class WHERE relname=%s", (self._table,))
        if cr.rowcount:
            self._update_operators_cache(cr)

    _columns = {
        'name': fields.char('Name', size=30, required=True),
        'symbol': fields.char('Symbol', size=8, required=True),
        'opposite_symbol': fields.char('Opposite symbol', size=12, help="Opposite symbol for SQL filter"),
        'value_age_filter': fields.selection([('current', 'Current'), ('old', 'Old'), ('both', 'Both')], 'Value Age Filter', required=True),
        'native_operator': fields.selection([('=', 'is equal to'), ('<=', 'less than'), ('>=', 'greater than'), ('like', 'contains'),
                                             ('ilike', 'contains exactly'), ('in', 'in'), ('child_of', 'child of'), ('none', 'none')], 'Native Operator'),
        'other_value_necessary': fields.boolean('Other Value Necessary'),
        'other_value_transformation': fields.char('Value Transformation', size=64, help="Useful only for native operator"),
        'expression': fields.text('Expression'),
    }

    _defaults = {
        'native_operator': lambda * a: 'none',
        'value_age_filter': lambda * a: 'both',
        'expression': lambda * a: """# You can use the following variables
\n#    - selected_field_value (current or old value according to the value age choosed by the user - value age filter == 'Both')
\n#    - current_field_value (useful if value age filter != 'Both')
\n#    - old_field_value (useful if value age filter != 'Both')
\n#    - other_value (static or dynamic)
\n# You must assign a boolean value to the variable "result"
""",
        'other_value_necessary': lambda * a: False,
    }

    def _update_operators_cache(self, cr):
        operator_ids = self.search(cr, 1, [])
        operators = self.browse(cr, 1, operator_ids)
        self.sartre_operators_cache = dict([(item.symbol, item) for item in operators])
        opposite_operators_dict = dict([(item.opposite_symbol, item) for item in operators])
        self.sartre_operators_cache.update(opposite_operators_dict)
        return True

    def sartre_operator_decorator(fnct):
        def new_fnct(self, cr, *args, **kwds):
            result = getattr(osv.osv, fnct.__name__)(self, cr, *args, **kwds)
            if result:
                self._update_operators_cache(cr)
            return result
        return new_fnct

    @sartre_operator_decorator
    def create(self, cr, uid, vals, context={}):
        return super(sartre_operator, self).create(cr, uid, vals, context)

    @sartre_operator_decorator
    def write(self, cr, uid, ids, vals, context={}):
        return super(sartre_operator, self).write(cr, uid, ids, vals, context)

    @sartre_operator_decorator
    def unlink(self, cr, uid, ids, context={}):
        return super(sartre_operator, self).unlink(cr, uid, ids, context)

sartre_operator()

class sartre_rule(osv.osv):
    _name = 'sartre.rule'
    _description = 'Sartre Rule'
    logger = netsvc.Logger()

    def __init__(self, pool, cr):
        super(sartre_rule, self).__init__(pool, cr)
        cr.execute("SELECT * FROM pg_class WHERE relname=%s", (self._table,))
        if cr.rowcount:
            self._update_rules_cache(cr)

    def _get_trigger_date_type(self, cr, uid, ids, name, args, context={}):
        """Get trigger date type"""
        res = {}
        if isinstance(ids, (int, long)):
            ids = [ids]
        for rule in self.browse(cr, uid, ids):
            if rule.trigger_date_type_display1 == 'other_date':
                res[rule.id] = rule.trigger_date_type_display2_id.name
            else:
                res[rule.id] = rule.trigger_date_type_display1
        return res

    def onchange_get_domain_force(self, cr, uid, ids, condition_ids, domain_force, context={}):
        """Build domain expression from conditions"""
        res = {}
        domain_force = domain_force and eval(domain_force) or []
        for condition in self.pool.get('sartre.condition').read(cr, uid, condition_ids, ['domain']):
            domain_force.extend(condition['domain'] and eval(condition['domain']) or [])
        res.setdefault('value', {})['domain_force'] = domain_force
        return res

    def onchange_model_id(self, cr, uid, ids, model_id, trigger_function, trigger_other, context={}):
        """Dynamic domain for the field trigger_function_field"""
        res = {'value': {'trigger_login_readonly': True}}
        if model_id:
            model = self.pool.get('ir.model').read(cr, uid, model_id, ['model'])['model']
            if model == 'res.users':
                res['value']['trigger_login_readonly'] = False
            obj = self.pool.get(model)
            if trigger_function:
                function_fields = [field for field in obj._columns if isinstance(obj._columns[field], (fields.function, fields.related, fields.property))]
                res.setdefault('domain', {})['trigger_function_field_id'] = "[('model_id', '=', %s),('name', 'in', %s)]" % (model_id, map(str, function_fields))
            if trigger_other:
                method_names = [attr for attr in dir(obj.__class__) if inspect.ismethod(getattr(obj, attr))]
                model_methods_pool = self.pool.get('ir.model.methods')
                model_methods_ids = model_methods_pool.search(cr, uid, [('model_id', '=', model_id), ('name', 'in', method_names)])
                existing_method_names = [method['name'] for method in model_methods_pool.read(cr, uid, model_methods_ids, ['name'])]
                for method in method_names:
                    method_args = inspect.getargspec(getattr(obj, method))[0]
                    if method not in ['create', 'write', 'unlink'] + existing_method_names and not method.startswith('__') and ('ids' in method_args or 'id' in method_args):
                        model_methods_pool.create(cr, uid, {'name': method, 'model_id': model_id})
        return res

    _columns = {
        'name': fields.char("Name", size=64, required=True),
        'model_id': fields.many2one('ir.model', 'Object', required=True, ondelete='cascade'),
        'active': fields.boolean("Active"),
        'trigger_create': fields.boolean("Creation"),
        'trigger_write': fields.boolean("Update"),
        'trigger_unlink': fields.boolean("Deletion"),
        'trigger_login': fields.boolean("Login", help="Works only with the model 'res.users'"),
        'trigger_login_readonly': fields.boolean("Trigger Login Readonly"),
        'trigger_function': fields.boolean("Function"),
        'trigger_function_type': fields.selection([('set', 'Manually'), ('get', 'Automatically'), ('both', 'Both')], "updated", size=16),
        'trigger_function_field_id': fields.many2one('ir.model.fields', "Function field", domain="[('model_id', '=', model_id)]", help="Function, related or property field"),
        'trigger_other': fields.boolean("Other methods", help="Only methods with an argument 'id' or 'ids' in their signatures"),
        'trigger_other_method_id': fields.many2one('ir.model.methods', "Object method", domain="[('model_id', '=', model_id)]"),
        'trigger_date': fields.boolean("Date"),
        'trigger_date_type': fields.function(_get_trigger_date_type, method=True, type='char', size=64, string='Trigger Date Type', store=True),
        'trigger_date_type_display1': fields.selection([('create_date', 'Creation Date'), ('write_date', 'Update Date'), ('other_date', 'Other Date')], 'Trigger Date Type 1', size=16),
        'trigger_date_type_display2_id': fields.many2one('ir.model.fields', 'Trigger Date Type 2', domain="[('ttype','in',['date','datetime']),('model_id','=',model_id)]"),
        'trigger_date_range': fields.integer('Delay'),
        'trigger_date_range_type': fields.selection([('minutes', 'Minutes'), ('hours', 'Hours'), ('work_days', 'Work Days'), ('days', 'Days'), ('weeks', 'Weeks'), ('months', 'Months')], 'Delay Type'),
        'trigger_date_range_operand': fields.selection([('after', 'After'), ('before', 'Before')], 'Delay Operand'),
        'interval_number': fields.integer('Interval Number'),
        'interval_type': fields.selection([('minutes', 'Minutes'), ('hours', 'Hours'), ('work_days', 'Work Days'), ('days', 'Days'), ('weeks', 'Weeks'), ('months', 'Months')], 'Interval Unit'),
        'nextcall': fields.datetime("Next Call"),
        'condition_ids': fields.one2many('sartre.condition', 'sartre_rule_id', "Conditions", help="The rule is satisfied if all conditions are True"),
        'domain_force': fields.char('Force Domain', size=250),
        'action_ids': fields.many2many('ir.actions.server', 'sartre_rule_server_action_rel', 'sartre_rule_id', 'server_action_id', "Actions"),
        'executions_max_number': fields.integer('Max executions', help="Number of time actions are runned,\0 indicates that actions will always be executed"),
    }

    _defaults = {
        'active': lambda * a: True,
        'trigger_function_type': lambda * a: 'both',
        'trigger_date_type_display1': lambda * a: 'create_date',
        'trigger_date_range': lambda * a: 2,
        'trigger_date_range_type': lambda * a: 'days',
        'trigger_date_range_operand': lambda * a: 'after',
        'interval_number': lambda * a: 1,
        'interval_type': lambda * a: 'hours',
        'nextcall': lambda * a: now().strftime("%Y-%m-%d %H:%M:%S"),
        'trigger_login_readonly': lambda * a: True,
    }

    def _update_rules_cache(self, cr):
        self.sartre_rules_cache = {}
        rule_ids = self.search(cr, 1, [], context={'active_test': True})
        rules = self.browse(cr, 1, rule_ids)
        for rule in rules:
            for method in ['create', 'write', 'unlink', 'function', 'login', 'other']: # All except for date
                if getattr(rule, 'trigger_' + method):
                    self.sartre_rules_cache.setdefault(method, {}).setdefault(rule.model_id.model, []).append(rule.id)
                    if method == 'other':
                        m_class = self.pool.get(rule.model_id.model)
                        m_name = rule.trigger_orther_method_id.name
                        if hasattr(m_class, m_name):
                            setattr(m_class, m_name, sartre_decorator(getattr(m_class, m_name)))
        return True

    def sartre_rule_decorator(fnct):
        def new_fnct(self, cr, *args, **kwds):
            result = getattr(osv.osv, fnct.__name__)(self, cr, *args, **kwds)
            if result:
                self._update_rules_cache(cr)
            return result
        return new_fnct

    @sartre_rule_decorator
    def create(self, cr, uid, vals, context={}):
        return super(sartre_rule, self).create(cr, uid, vals, context)

    @sartre_rule_decorator
    def write(self, cr, uid, ids, vals, context={}):
        return super(sartre_rule, self).write(cr, uid, ids, vals, context)

    @sartre_rule_decorator
    def unlink(self, cr, uid, ids, context={}):
        return super(sartre_rule, self).unlink(cr, uid, ids, context)

    def _add_trigger_date_condition(self, cr, uid, rule, context={}):
        """Build trigger date condition"""
        res = False
        if rule.trigger_date:
            interval_number = rule.trigger_date_range
            interval_type = str(rule.trigger_date_range_type)
            interval_operand = rule.trigger_date_range_operand
            # Update rule next call
            self.write(cr, uid, rule.id, {'nextcall': now() + RelativeDateTime(**{str(rule.interval_type): rule.interval_number})}, context)
            # Add datetime filter
            field = rule.trigger_date_type
            limit_date = now()
            if interval_operand == 'after':
                limit_date -= RelativeDateTime(**{interval_type: interval_number})
            if interval_operand == 'before':
                limit_date += RelativeDateTime(**{interval_type: interval_number})
            res = (field, '<=', limit_date.strftime("%Y-%m-%d %H:%M:%S"))
        return res

    def _add_max_executions_condition(self, cr, uid, rule, context={}):
        """Build max executions condition"""
        res = False
        if rule.executions_max_number:
            execution_pool = self.pool.get('sartre.execution')
            execution_ids = execution_pool.search(cr, uid, [('rule_id', '=', rule.id), ('executions_number', '>=', rule.executions_max_number)])
            res_ids = list(set(context.get('active_object_ids', [])) - set([execution['res_id'] for execution in execution_pool.read(cr, uid, execution_ids, ['res_id'])]))
            res = ('id', 'in', res_ids)
        return res

    def _build_domain_expression(self, cr, uid, rule, context={}):
        """Build domain expression"""
        # To manage planned execution
        if not context.get('active_object_ids', []):
            context['active_object_ids'] = self.pool.get(rule.model_id.model).search(cr, uid, [], context=context)
        operators_cache = self.pool.get('sartre.operator').sartre_operators_cache
        # Define domain from domain_force
        domain = rule.domain_force and eval(rule.domain_force.replace('%today', now().strftime('%Y-%m-%d %H:%M:%S'))) or []
        # Add conditions one by one if domain_force is empty
        if not domain:
            domain.extend(sum(map(lambda cond: eval(cond.domain.replace('%today', now().strftime('%Y-%m-%d %H:%M:%S'))), rule.condition_ids), []))
        # Add general conditions
        domain.extend(filter(bool, [getattr(self, condition_name)(cr, uid, rule, context) for condition_name in ['_add_trigger_date_condition', '_add_max_executions_condition']]))
        # To avoid infinite recursion
        if 'rules' in context and rule.id in context['rules']:
            context['active_object_ids'] = list(set(context['active_object_ids']) - set(context['rules'][rule.id]))
        # Check if active objects respect all conditions based on old or dynamic values, or python operators
        indexes = [domain.index(item) for item in domain if isinstance(item, tuple) and (item[0].startswith('OLD_') or operators_cache[item[1]].native_operator == 'none' or re.match('(\[\[.+?\]\])', str(item[2]) or ''))]
        if not indexes:
            domain.append(('id', 'in', context['active_object_ids']))
        else:
            fields = [domain[index][0].replace('OLD_', '') for index in indexes]
            old_values = context.get('old_values', {})
            current_values = _get_browse_record_dict(self.pool.get(rule.model_id.model), cr, uid, context['active_object_ids'])
            # Replace filters on old values or Python operators by filters on active objects
            for index in indexes:
                active_object_ids = list(set(context['active_object_ids']))
                condition = domain[index]
                field = condition[0].replace('OLD_', '')
                prefix = ''
                operator_symbol = condition[1]
                if operator_symbol.startswith('not '): # Can accept 'not ==' instead of '<>' but can't accept '!='
                    prefix = 'not '
                    operator_symbol = operator_symbol.replace('not ', '')
                prefix += operator_symbol == operators_cache[condition[1]].opposite_symbol and 'not ' or '' # += rather than = in order to manage double negation
                other_value = condition[2]
                match = other_value and re.match('(\[\[.+?\]\])', other_value)
                for object_id in list(active_object_ids):
                    if match:
                        other_value = eval(str(match.group()[2:-2]).strip(), {
                            'object': self.pool.get(rule.model_id.model).browse(cr, uid, object_id),
                            'context': context,
                            'time':time})
                    current_field_value = current_values.get(object_id, {}).get(field, False)
                    old_field_value = current_field_value
                    if object_id in old_values and field in old_values[object_id]:
                        old_field_value = old_values[object_id][field]
                    localdict = {'selected_field_value': 'OLD_' in condition[0] and old_field_value or current_field_value,
                                 'current_field_value': current_field_value,
                                 'old_field_value': old_field_value,
                                 'other_value': other_value}
                    exec operators_cache[operator_symbol].expression in localdict
                    if 'result' not in localdict or ('result' in localdict and (prefix and localdict['result'] or not localdict['result'])):
                        active_object_ids.remove(object_id)
                domain[index] = ('id', 'in', active_object_ids)
        return domain

    def run_now(self, cr, uid, ids, context=None):
        """Execute now server actions"""
        if context is None:
            context_copy = {}
        else:
            context_copy = dict(context)
        context_copy.setdefault('active_test', False)
        for rule in self.browse(cr, uid, ids):
            self.logger.notifyChannel('sartre.rule', netsvc.LOG_DEBUG, 'Rule: %s, User: %s' % (rule.id, uid))
            domain = []
            domain_built = False
            try:
                # Build domain expression
                domain = self._build_domain_expression(cr, uid, rule, context_copy)
                domain_built = True
            except Exception, e:
                stack = traceback.format_exc()
                self.pool.get('sartre.exception').create(cr, uid, {'rule_id': rule.id, 'exception_type': 'condition', 'exception': tools.ustr(e), 'stack': tools.ustr(stack)})
                self.logger.notifyChannel('sartre.rule', netsvc.LOG_ERROR, 'Rule: %s, User: %s, Exception:%s' % (rule.id, uid, tools.ustr(e)))
            # Search action to execute for filtered objects from domain
            if domain_built:
                # Search objects which validate rule conditions
                rule_object_ids = self.pool.get(rule.model_id.model).search(cr, uid, domain, context=context_copy)
                # Execute server actions
                if rule_object_ids:
                    context_copy.setdefault('rules', {}).setdefault(rule.id, []).extend(rule_object_ids)
                    ir_actions_server_pool = self.pool.get('ir.actions.server')
                    for action in rule.action_ids:
                        if action.active:
                            try:
                                if action.run_once:
                                    # Sartre case where you run once for all instances
                                    context_copy['active_id'] = rule_object_ids
                                    ir_actions_server_pool.run(cr, action.user_id and action.user_id.id or uid, [action.id], context=context_copy)
                                    self.logger.notifyChannel('ir.actions.server', netsvc.LOG_DEBUG, 'Action: %s, User: %s, Resource: %s, Origin: sartre.rule,%s' % (action.id, action.user_id and action.user_id.id or uid, context_copy['active_id'], rule.id))
                                else:
                                    # Sartre case where you run once per instance
                                    for object_id in rule_object_ids:
                                        context_copy['active_id'] = object_id
                                        ir_actions_server_pool.run(cr, action.user_id and action.user_id.id or uid, [action.id], context=context_copy)
                                        self.logger.notifyChannel('ir.actions.server', netsvc.LOG_DEBUG, 'Action: %s, User: %s, Resource: %s, Origin: sartre.rule,%s' % (action.id, action.user_id and action.user_id.id or uid, context_copy['active_id'], rule.id))
                                if rule.executions_max_number:
                                    for object_id in rule_object_ids:
                                        self.pool.get('sartre.execution').update_executions_counter(cr, uid, rule, object_id)
                            except Exception, e:
                                stack = traceback.format_exc()
                                self.pool.get('sartre.exception').create(cr, uid, {'rule_id': rule.id, 'exception_type': 'action', 'res_id': False, 'action_id': action.id, 'exception': tools.ustr(e), 'stack': tools.ustr(stack)})
                                self.logger.notifyChannel('ir.actions.server', netsvc.LOG_ERROR, 'Action: %s, User: %s, Resource: %s, Origin: sartre.rule,%s, Exception: %s' % (action.id, action.user_id and action.user_id.id or uid, False, rule.id, tools.ustr(e)))
                                continue
        return True

    def check_rules(self, cr, uid, context={}):
        """Call the scheduler to check date based trigger rules"""
        # Search rules to execute
        rule_ids = self.search(cr, uid, [('active', '=', True), ('trigger_date', '=', True), ('nextcall', '<=', now().strftime("%Y-%m-%d %H:%M:%S"))])
        if rule_ids:
            # Launch rules execution
            self.run_now(cr, uid, rule_ids, context)
        return True

sartre_rule()

class sartre_condition(osv.osv):
    _name = 'sartre.condition'
    _description = 'Sartre Condition'
    _rec_name = 'field_id'

    def onchange_get_domain(self, cr, uid, ids, field='', operator_id=False, opposite=False, value='', value_age='current', value_type='static', context={}):
        """Build domain expression from condition items"""
        res = {}
        if field and operator_id and (value or not self.pool.get('sartre.operator').read(cr, uid, operator_id, ['other_value_necessary'])['other_value_necessary']):
            field_name = (value_age == 'old' and 'OLD_' or '') + field
            operator = self.pool.get('sartre.operator').browse(cr, uid, operator_id)
            symbol = opposite and operator.opposite_symbol or operator.symbol
            if not isinstance(value, (str, unicode)):
                value = ''
            if value_age == 'current' and value_type == 'static':
                value = operator.other_value_transformation and eval(operator.other_value_transformation, {'value': value}) or value
            if value_type == 'dynamic' and value:
                value = '[[ object.' + value + ' ]]'
            res['value'] = {'domain': str([(field_name, symbol, value)])}
        return res

    def _build_field_expression(self, cr, uid, field_id, field_expression='', context={}):
        """Build field expression"""
        field_pool = self.pool.get('ir.model.fields')
        field_obj = field_pool.read(cr, uid, field_id, ['name', 'ttype', 'relation', 'model'])
        field_expr = field_expression and (field_expression.split('.')[:-1] and '.'.join(field_expression.split('.')[:-1]) or field_expression) + '.' or ''
        obj = self.pool.get(field_obj['model'])
        if field_obj['name'] in obj._columns and 'fields.related' in str(obj._columns[field_obj['name']]):
            field_expr += obj._columns[field_obj['name']].arg[0] + '.'
        field_expr += field_obj['name']
        if field_obj['ttype'] in ['many2one', 'one2many', 'many2many']:
            field_expr += field_obj['ttype'] == 'many2one' and '.'  or ''
            field_expr += field_obj['ttype'] in ['one2many', 'many2many'] and '[0].' or ''
            field_expr += self.pool.get(field_obj['relation'])._rec_name
        return field_expr

    def _check_field_expression(self, cr, uid, model_id, field_expression='', context={}):
        """Check field expression"""
        field_list = field_expression and (field_expression.split('.')[:-1] or [field_expression])
        if field_list:
            field_pool = self.pool.get('ir.model.fields')
            model = self.pool.get('ir.model').read(cr, uid, model_id, ['model'])['model']
            i = 0
            for f_name in field_list:
                f_id = field_pool.search(cr, uid, [('model', '=', model), ('name', '=', '[' in f_name and f_name[:f_name.index('[')] or f_name)], limit=1)
                if not f_id:
                    raise osv.except_osv(_('Error'), _("The field %s is not in the model %s !" % (f_name, model)))
                f_obj = field_pool.read(cr, uid, f_id[0], ['name', 'ttype', 'relation'])
                if f_obj['ttype'] in ['many2one', 'one2many', 'many2many']:
                    model = f_obj['relation']
                    model_id = self.pool.get('ir.model').search(cr, uid, [('model', '=', model)], limit=1)[0]
                elif len(field_expression.split('.')) > 1 and  i < len(field_list):
                    raise osv.except_osv(_('Error'), _("The field %s is not a relation field !" % f_obj['name']))
                i += 1
        return model_id

    def onchange_get_field_domain(self, cr, uid, ids, model_id, field_expression='', context={}):
        """Get field domain"""
        model_id = self._check_field_expression(cr, uid, model_id, field_expression, context)
        res = {'values': {'field_id': False}, 'domain': {'field_id': "[('model_id', '=', %d)]" % (model_id,)}}
        return res

    def onchange_get_field_expression(self, cr, uid, ids, model_id, field_expression='', field_id=False, context={}):
        """Update the field expression"""
        new_field_expression = field_expression
        if field_id:
            new_field_expression = self._build_field_expression(cr, uid, field_id, field_expression, context)
        res = self.onchange_get_field_domain(cr, uid, ids, model_id, new_field_expression, context)
        res.setdefault('value', {}).update({'field_expression': new_field_expression})
        return res

    def onchange_get_value_age_domain(self, cr, uid, ids, field='', operator_id=False, opposite=False, value='', value_age='current', value_type='static', context={}):
        """Update the field 'value_age'"""
        value_age_filter = operator_id and self.pool.get('sartre.operator').read(cr, uid, operator_id, ['value_age_filter'])['value_age_filter']
        if value_age_filter != 'both':
            value_age = value_age_filter
        res = self.onchange_get_domain(cr, uid, ids, field, operator_id, opposite, value, value_age, value_type, context)
        res.setdefault('value', {})
        res['value'] = {'value_age': value_age, 'value_age_readonly': value_age_filter != 'both'}
        return res

    _columns = {
        "sartre_rule_id": fields.many2one('sartre.rule', "Rule", required=True, ondelete='cascade'),
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
        'value_age': lambda * a: 'current',
        'value_type': lambda * a: 'static',
    }

sartre_condition()

class sartre_exception(osv.osv):
    _name = 'sartre.exception'
    _description = 'Sartre Exception'
    _rec_name = 'rule_id'

    _columns = {
        'rule_id': fields.many2one('sartre.rule', 'Rule', required=False, select=True),
        'exception_type': fields.selection([
            ('condition', 'Condition'),
            ('action', 'Action'),
             ], 'Type', required=False, select=True),
        'res_id': fields.integer('Resource', required=False),
        'action_id': fields.many2one('ir.actions.server', 'Action', required=False, select=True),
        'exception': fields.text('Exception', required=False),
        'stack': fields.text('Stack Trace', required=False),
        'create_date': fields.datetime('Creation Date'),
    }

    _order = "create_date desc"

sartre_exception()

class sartre_execution(osv.osv):
    _name = 'sartre.execution'
    _description = 'Sartre Execution'
    _rec_name = 'rule_id'

    _columns = {
        'rule_id': fields.many2one('sartre.rule', 'Rule', required=False, select=True),
        'model_id': fields.many2one('ir.model', 'Object', required=False, select=True),
        'res_id': fields.integer('Resource', required=False),
        'executions_number': fields.integer('Executions'),
    }

    def update_executions_counter(self, cr, uid, rule, res_id):
        """Update executions counter"""
        if not (rule and res_id):
            raise osv.except_osv(_('Error'), _('Sartre Execution: all arguments are mandatory !'))
        log_id = self.search(cr, uid, [('rule_id', '=', rule.id), ('model_id', '=', rule.model_id.id), ('res_id', '=', res_id)], limit=1)
        if log_id:
            executions_number = self.read(cr, uid, log_id[0], ['executions_number'])['executions_number'] + 1
            return self.write(cr, uid, log_id[0], {'executions_number': executions_number})
        else:
            return self.create(cr, uid, {'rule_id': rule.id, 'model_id': rule.model_id.id, 'res_id': res_id, 'executions_number': 1}) and True

sartre_execution()

def _check_method_based_trigger_rules(self, cr, uid, method, field_name='', calculation_method=False):
    """Check method based trigger rules"""
    rule_ids = []
    rule_obj = hasattr(self, 'pool') and self.pool.get('sartre.rule') or pooler.get_pool(cr.dbname).get('sartre.rule')
    if rule_obj:
        # Search rules to execute
        rule_ids += hasattr(rule_obj, 'sartre_rules_cache') and method in rule_obj.sartre_rules_cache and self._name in rule_obj.sartre_rules_cache[method] and rule_obj.sartre_rules_cache[method][self._name] or []
        if method == 'function':
            for rule_id in rule_ids:
                rule = rule_obj.browse(cr, uid, rule_id)
                if not (rule.trigger_function_field_id.name == field_name and rule.trigger_function_type in [calculation_method, 'both']):
                    rule_ids.remove(rule_id)
    return rule_ids

def sartre_decorator(original_method):
    def sartre_trigger(*args, **kwds):
        # Get arguments
        method_name = original_method.__name__
        args_names = inspect.getargspec(original_method)[0]
        args_dict = {}.fromkeys(args_names, False)
        for arg in args_names:
            if args_names.index(arg) < len(args):
                args_dict[arg] = args[args_names.index(arg)]
        self = args_dict.get('obj', False) or args_dict.get('self', False)
        cr = args_dict.get('cursor', False) or args_dict.get('cr', False)
        uid = args_dict.get('uid', False) or args_dict.get('user', False)
        ids = args_dict.get('ids', []) or args_dict.get('id', [])
        if isinstance(ids, (int, long)):
            ids = [ids]
        context = dict(args_dict.get('context', {}) or {})
        args_ok = reduce(operator.__and__, map(bool, [self, cr, uid]))
        if args_ok:
            # Case: trigger on function
            field_name = ''
            calculation_method = False
            if method_name in ('get', 'set') and original_method.im_class == fields.function:
                field_name = args_dict.get('name', '')
                calculation_method = method_name
                method_name = 'function'
            # Search trigger rules
            rule_ids = _check_method_based_trigger_rules(self, cr, uid, original_method.__name__)
            # Save old values if trigger rules exist
            if rule_ids and ids:
                context.update({'active_object_ids': ids, 'old_values': _get_browse_record_dict(self, cr, uid, ids)})
                # Case: trigger on unlink
                if original_method.__name__ == 'unlink':
                    self.pool.get('sartre.rule').run_now(cr, uid, rule_ids, context=context)
        # Execute original method
        result = original_method(*args, **kwds)
        # Run trigger rules if exists
        if result and args_ok and rule_ids and original_method.__name__ != 'unlink':
            # Case: trigger on create
            if original_method.__name__ == 'create':
                context['active_object_ids'] = [result]
            self.pool.get('sartre.rule').run_now(cr, uid, rule_ids, context=context)
        return result
    return sartre_trigger

for method in [orm.orm.create, orm.orm.write, orm.orm.unlink, fields.function.get, fields.function.set]:
    if hasattr(method.im_class, method.__name__):
        setattr(method.im_class, method.__name__, sartre_decorator(getattr(method.im_class, method.__name__)))

common = netsvc.SERVICES['common'].__class__

class sartre_common(common):

    def login(self, db, login, password):
        """Override common login method"""
        uid = super(sartre_common, self).login(db, login, password)
        if uid:
            pool = pooler.get_pool(db)
            cr = pooler.get_db(db).cursor()
            try:
                rule_ids = _check_method_based_trigger_rules(pool.get('res.users'), cr, uid, 'login')
                if rule_ids:
                    self.pool.get('sartre.rule').run_now(cr, uid, rule_ids, context={'active_object_ids': list(uid)})
            finally:
                cr.close()
        return uid

sartre_common()
