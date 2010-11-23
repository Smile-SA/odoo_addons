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

from osv import osv, fields, orm
from tools.translate import _
import operator
import traceback
import time
import pooler
import netsvc

class checklist(osv.osv):
    _name = 'checklist'
    _description = 'Checklist'

    _columns = {
        'name':fields.char('Name', size=128, required=True, translate=True),
        'model_id':fields.many2one('ir.model', 'Model', required=True),
        'model': fields.related('model_id', 'model', type='char', size=64, string='Model Name'),
        'active': fields.boolean('Active'),
        'active_field': fields.boolean("Add or update a boolean field 'Active' in model"),
        'action_id': fields.many2one('ir.actions.server', 'Actions'),
        'view_ids': fields.many2many('ir.ui.view', 'checklist_view_rel', 'view_id', 'checklist_id', 'Views'),
    }

    _defaults = {
        'active': lambda * a: True,
    }

    def _check_unique_checklist_per_object(self, cr, uid, ids): 
        if isinstance(ids, (int, long)):
            ids = [ids]
        for checklist in self.browse(cr, uid, ids):
            checklist_ids = self.search(cr, uid, [('model_id', '=', checklist.model_id.id)])
            if len(checklist_ids) > 1:
                return False
        return True

    _constraints = [(_check_unique_checklist_per_object, "A checklist has already existed for this model !", ['model_id'])]
checklist()

class checklist_task(osv.osv):
    _name = 'checklist.task'
    _description = 'Checklist Task'

    _columns = {
        'name':fields.char('Name', size=128, required=True, translate=True),
        'checklist_id':fields.many2one('checklist', 'Checklist', required=True, ondelete='cascade'),
        'model_id': fields.related('checklist_id', 'model_id', type='many2one', relation='ir.model', string='Model'),
        'condition': fields.char('Condition', size=256, required=True),
        'active': fields.boolean('Active'),
        'action_id': fields.many2one('ir.actions.server', 'Action'),
        'sequence': fields.integer('Priority', required=True),
        'active_field': fields.related('checklist_id', 'active_field', type='boolean', string="Field 'Active'"),
        'mandatory': fields.boolean('Required to make active object'),
    }

    _defaults = {
        'condition': lambda * a: 'True',
        'active': lambda * a: True,
        'sequence': lambda * a: 15,
    }
checklist_task()

class checklist_task_field(osv.osv):
    _name = 'checklist.task.field'
    _description = 'Checklist Task Field'

    def _build_field_expression(self, cr, uid, field_id, field_name='', context={}):
        """Build field expression"""
        field_name = field_name and field_name.replace('object.', '')
        field_pool = self.pool.get('ir.model.fields')
        field_obj = field_pool.read(cr, uid, field_id, ['name', 'ttype', 'relation', 'model'])
        field_expr = field_name and (field_name.split('.')[:-1] and '.'.join(field_name.split('.')[:-1]) or field_name) + '.' or ''
        obj = self.pool.get(field_obj['model'])
        if field_obj['name'] in obj._columns and 'fields.related' in str(obj._columns[field_obj['name']]):
            field_expr += obj._columns[field_obj['name']].arg[0] + '.'
        field_expr += field_obj['name']
        if field_obj['ttype'] in ['many2one', 'one2many', 'many2many']:
            field_expr += field_obj['ttype'] == 'many2one' and '.'  or ''
            field_expr += field_obj['ttype'] in ['one2many', 'many2many'] and '[0].' or ''
            field_expr += self.pool.get(field_obj['relation'])._rec_name
        return 'object.' + field_expr

    def _check_field_expression(self, cr, uid, model_id, field_name='', context={}):
        """Check field expression"""
        field_list = field_name and (field_name.replace('object.', '').split('.')[:-1] or [field_name.replace('object.', '')])
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
                elif len(f_name.split('.')) > 1 and  i < len(field_list):
                    raise osv.except_osv(_('Error'), _("The field %s is not a relation field !" % f_obj['name']))
                i += 1
        return model_id

    def onchange_get_field_domain(self, cr, uid, ids, model_id, expression='', field_id=False, context={}):
        """Get field domain"""
        model_id = self._check_field_expression(cr, uid, model_id, expression, context)
        return {'domain': {'field_id': "[('model_id','='," + str(model_id) + ")]"}}

    def onchange_get_field_expression(self, cr, uid, ids, model_id, expression='', field_id=False, context={}):
        """Update the field expression"""
        field_expr = expression
        if field_id:
            field_expr = self._build_field_expression(cr, uid, field_id, expression, context)
        res = self.onchange_get_field_domain(cr, uid, ids, model_id, field_expr, False, context)
        if field_id:
            field_description = self.pool.get('ir.model.fields').read(cr, uid, field_id, ['field_description'])['field_description']
            #res.setdefault('value', {}).update({'name': field_description})
        res.setdefault('value', {}).update({'field_name': field_expr})
        return res

    _columns = {
        'name': fields.char('Name', size=128, required=True, translate=True),
        'expression': fields.text('Expression', required=True),
        'field_name': fields.char('Copy to expression field', size=128),
        'field_id': fields.many2one('ir.model.fields', "Choose a field"),
        'task_id': fields.many2one('checklist.task', 'Task'),
    }
checklist_task_field()

class checklist_task(osv.osv):
    _name = 'checklist.task'
    _inherit = 'checklist.task'

    _columns = {
        'field_ids': fields.one2many('checklist.task.field', 'task_id', 'Fields', required=True),
    }

    def create(self, cr, uid, vals, context=None):
        checklist_task_id = super(checklist_task, self).create(cr, uid, vals, context)
        checklist_task_obj = self.browse(cr, uid, checklist_task_id)
        model = self.pool.get(checklist_task_obj.checklist_id.model_id.model)
        for object_id in model.search(cr, uid, [], context={'active_test': False}):
            self.pool.get('checklist.task.instance').create(cr, uid, {'checklist_task_id': checklist_task_id, 'res_id':object_id}, context=context)
        self.pool.get('checklist')._compute_progress_rates(model, cr, uid)
        return checklist_task_id

    def write(self, cr, uid, ids, vals, context=None):
        result = super(checklist_task, self).write(cr, uid, ids, vals, context)
        if isinstance(ids, (int, long)):
            ids = [ids]
        models = []
        for checklist_task_obj in self.browse(cr, uid, ids):
            models.append(self.pool.get(checklist_task_obj.checklist_id.model_id.model))
        for model in list(set(models)):
            self.pool.get('checklist')._compute_progress_rates(model, cr, uid)
        return result

    def unlink(self, cr, uid, ids, context=None):
        if isinstance(ids, (int, long)):
            ids = [ids]
        models = []
        for checklist_task_obj in self.browse(cr, uid, ids):
            models.append(self.pool.get(checklist_task_obj.checklist_id.model_id.model))
        result = super(checklist_task, self).unlink(cr, uid, ids, context)
        for model in list(set(models)):
            self.pool.get('checklist')._compute_progress_rates(model, cr, uid)
        return result
checklist_task()

class checklist(osv.osv):
    _name = 'checklist'
    _inherit = 'checklist'
    logger = netsvc.Logger()

    _columns = {
        'task_ids': fields.one2many('checklist.task', 'checklist_id', 'Tasks'),
    }

    def _get_checklist_task_instances(self, obj, cr, uid, ids, multi, arg, context=None):
        if isinstance(ids, (int, long)):
            ids = [ids]
        res = {}
        for id in ids:
            checklist_task_instance_ids = obj.pool.get('checklist.task.instance').search(cr, uid, [('checklist_task_id.checklist_id.model_id.model', '=', obj._name), ('res_id', '=', id)], context={'active_test': True})
            # The next line exists because of a bug in orm
            res[id] = [inst['id'] for inst in obj.pool.get('checklist.task.instance').read(cr, uid, checklist_task_instance_ids, ['active']) if inst['active']]
        return res

    def _update_checklists_cache(self, cr):
        self.checklists_cache = {}
        checklist_ids = self.search(cr, 1, [])
        if checklist_ids:
            for checklist in self.browse(cr, 1, checklist_ids):
                self.checklists_cache[checklist.model_id.model] = checklist.id
        return True

    def _update_models(self, cr, models={}):
        if not models:
            checklist_ids = self.search(cr, 1, [])
            models = dict([(checklist['model_id'][0], {'checklist_id': checklist['id'], 'active_field': checklist['active_field']}) for checklist in self.read(cr, 1, checklist_ids, ['model_id', 'active_field'])])
        for model in self.pool.get('ir.model').read(cr, 1, models.keys(), ['model']):
            if self.pool.get(model['model']):
                model_columns = self.pool.get(model['model'])._columns
                checklist_id = models[model['id']] and models[model['id']].get('checklist_id', False)
                if checklist_id:
                    model_columns.update({
                        'checklist_task_instance_ids': fields.function(self._get_checklist_task_instances, method=True, type='one2many', relation='checklist.task.instance', string='Checklist Task Instances', store=False),
                        'total_progress_rate': fields.float('Progress Rate', digits=(16, 2)),
                    })
                    columns_to_add = {'total_progress_rate': 'NUMERIC(16,2)'}
                    if models[model['id']].get('active_field', False):
                        model_columns.update({'active': fields.boolean('Active'), 'total_progress_rate_mandatory': fields.float('Mandatory Progress Rate', digits=(16, 2))})
                        columns_to_add.update({'active': 'BOOLEAN', 'total_progress_rate_mandatory': 'NUMERIC(16,2)'})
                    for column in columns_to_add:
                        cr.execute("""SELECT c.relname FROM pg_class c, pg_attribute a
                                      WHERE c.relname=%s AND a.attname=%s AND c.oid=a.attrelid""", (model['model'].replace('.', '_'), column))
                        if not cr.rowcount:
                            cr.execute('ALTER TABLE "%s" ADD COLUMN "%s" %s' % (model['model'].replace('.', '_'), column, columns_to_add[column]))
                            cr.commit()
                else:
                    if 'checklist_task_instance_ids' in model_columns:
                        del model_columns['checklist_task_instance_ids']
                    if 'total_progress_rate' in model_columns:
                        del model_columns['total_progress_rate']
        return self._update_checklists_cache(cr)

    def __init__(self, pool, cr):
        super(checklist, self).__init__(pool, cr)
        cr.execute("SELECT * FROM pg_class WHERE relname=%s", (self._table,))
        if cr.rowcount:
            self._update_models(cr)

    def create(self, cr, uid, vals, context=None):
        checklist_id = super(checklist, self).create(cr, uid, vals, context)
        self._update_models(cr, {vals['model_id']: {'checklist_id': checklist_id, 'active_field': vals.get('active_field', False)}})
        return checklist_id

    def write(self, cr, uid, ids, vals, context=None):
        if 'model_id' in vals:
            if vals['model_id']:
                checklist = self.read(cr, uid, isinstance(ids, list) and ids[0] or ids, ['model_id', 'active_field'])
                models = {checklist['model_id'][0]: {'checklist_id': False, 'active_field': False}}
                models.update({vals['model_id']: {'checklist_id': checklist['id'], 'active_field': checklist['active_field']}})
            else:
                models = dict([(checklist_obj['model_id'][0], {'checklist_id': False, 'active_field': False}) for checklist_obj in self.read(cr, uid, ids, ['model_id'])])
        result = super(osv.osv, self).write(cr, uid, ids, vals, context)
        if 'model_id' in vals:
            self._update_models(cr, models)
        return result

    def unlink(self, cr, uid, ids, context=None):
        models = dict([(checklist_obj['model_id'][0], {'checklist_id': False, 'active_field': False}) for checklist_obj in self.read(cr, uid, ids, ['model_id'])])
        result = super(checklist, self).unlink(cr, uid, ids, context)
        self._update_models(cr, models)
        return result

    def _compute_progress_rates(self, obj, cr, uid, ids=[], context={}):
        if not ids:
            ids = obj.search(cr, uid, [])
        if isinstance(ids, (int, long)):
            ids = [ids]
        res = {}
        for object in obj.browse(cr, uid, ids):
            context['active_id'] = object.id
            instance_pool = self.pool.get('checklist.task.instance')
            instance_ids = instance_pool.search(cr, uid, [('checklist_task_id.checklist_id.model_id.model', '=', obj._name), ('res_id', '=', object.id)], context={'active_test': True})
            # The following line exists because of a bug in ORM
            instance_ids = [inst['id'] for inst in instance_pool.read(cr, uid, instance_ids, ['active']) if inst['active']]
            instances = instance_pool.browse(cr, uid, instance_ids)
            total_progress_rate = total_progress_rate_mandatory = 100
            total_progress_rates = {}
            checklist_filling = []
            for instance in instances:
                progress_rate = 100
                if instance.checklist_task_id.field_ids:
                    progress_rate -= (float(len(instance.field_ids_to_fill)) / float(len(instance.checklist_task_id.field_ids))) * 100
                instance_pool.write(cr, uid, instance.id, {'progress_rate': progress_rate})
                total_progress_rates.setdefault('total_progress_rate', 0.0)
                total_progress_rates.setdefault('instances_count', 0)
                total_progress_rates['total_progress_rate'] += progress_rate
                total_progress_rates['instances_count'] += 1
                if instance.checklist_task_id.action_id and instance.progress_rate != progress_rate == 100:
                    checklist_task = instance.checklist_task_id
                    action = instance.checklist_task_id.action_id
                    try:
                        self.pool.get('ir.actions.server').run(cr, uid, [action.id], context)
                        self.logger.notifyChannel('ir.actions.server', netsvc.LOG_DEBUG, 'Action: %s, User: %s, Resource: %s, Origin: checklist.task,%s' % (action.id, uid, object.id, checklist_task.id))
                    except Exception, e:
                        stack = traceback.format_exc()
                        self.pool.get('checklist.exception').create(cr, uid, {'checklist_task_id': checklist_task.id, 'exception_type': 'action', 'res_id': object.id, 'action_id': action.id, 'exception': e, 'stack': stack})
                        self.logger.notifyChannel('ir.actions.server', netsvc.LOG_ERROR, 'Action: %s, User: %s, Resource: %s, Origin: checklist.task,%s, Exception: %s' % (action.id, uid, object.id, checklist_task.id, tools.ustr(e)))
                        continue
                if instance.checklist_task_id.checklist_id.active_field and instance.mandatory:
                    total_progress_rates.setdefault('total_progress_rate_mandatory', 0.0)
                    total_progress_rates['total_progress_rate_mandatory'] += progress_rate
                    total_progress_rates.setdefault('instances_count_mandatory', 0)
                    total_progress_rates['instances_count_mandatory'] += 1
            if total_progress_rates.get('instances_count', False):
                total_progress_rate = total_progress_rates['total_progress_rate'] / total_progress_rates['instances_count']
            fields = ['total_progress_rate']
            values = ["%.2f" % total_progress_rate]
            if instances and instances[0].checklist_task_id.checklist_id.active_field:
                if total_progress_rates.get('instances_count_mandatory', False):
                    total_progress_rate_mandatory = total_progress_rates['total_progress_rate_mandatory'] / total_progress_rates['instances_count_mandatory']
                fields.append('total_progress_rate_mandatory')
                values.append("%.2f" % total_progress_rate_mandatory)
                if object.total_progress_rate_mandatory != total_progress_rate_mandatory == 100:
                    fields.append('active')
                    values.append("TRUE")
            cr.execute("UPDATE "+obj._table+" SET ("+','.join(fields)+") = %s WHERE id = %s", (tuple(values), object.id))
            if instances and instances[0].checklist_task_id.checklist_id.action_id and object.total_progress_rate != total_progress_rate == 100:
                checklist = instances[0].checklist_task_id.checklist_id
                action = checklist.action_id
                try:
                    self.pool.get('ir.actions.server').run(cr, uid, [action.id], context)
                    self.logger.notifyChannel('ir.actions.server', netsvc.LOG_DEBUG, 'Action: %s, User: %s, Resource: %s, Origin: checklist,%s' % (action.id, uid, object.id, checklist.id))
                except Exception, e:
                    stack = traceback.format_exc()
                    self.pool.get('checklist.exception').create(cr, uid, {'checklist_id': checklist.id, 'exception_type': 'action', 'res_id': object.id, 'action_id': action.id, 'exception': e, 'stack': stack})
                    self.logger.notifyChannel('ir.actions.server', netsvc.LOG_ERROR, 'Action: %s, User: %s, Resource: %s, Origin: checklist,%s, Exception: %s' % (action.id, uid, object.id, checklist.id, tools.ustr(e)))
                    continue
        return True

checklist()

class checklist_task_instance(osv.osv):
    _name = 'checklist.task.instance'
    _description = 'Checklist Task Instance'

    def _get_activity(self, cr, uid, ids, multi, arg, context=None):
        if isinstance(ids, (int, long)):
            ids = [ids]
        res = {}
        for instance in self.pool.get('checklist.task.instance').browse(cr, uid, ids, context=context):
            res[instance.id] = {'active': False, 'field_ids_to_fill': [], 'field_ids_filled': [], 'sequence': 15}
            localdict = {'object': self.pool.get(instance.checklist_task_id.checklist_id.model_id.model).browse(cr, uid, instance.res_id),
                         'time': time}
            res[instance.id]['active'] = instance.checklist_task_id.active and eval(instance.checklist_task_id.condition, localdict)
            res[instance.id]['sequence'] = instance.checklist_task_id.sequence
            for field in instance.checklist_task_id.field_ids:
                try:
                    exec "result = bool(%s)" % str(field.expression) in localdict
                    if 'result' not in localdict or not localdict['result']:
                        res[instance.id]['field_ids_to_fill'].append(field.id)
                    else:
                        res[instance.id]['field_ids_filled'].append(field.id)
                except Exception, e:
                    stack = traceback.format_exc()
                    self.pool.get('checklist.exception').create(cr, uid, {'checklist_task_id': instance.checklist_task_id.id, 'exception_type': 'field', 'res_id': instance.res_id, 'field_id': field.id, 'exception': e, 'stack': stack})
                    continue
        return res

    def _get_checklist_task_instance_ids(self, cr, uid, ids, context={}):
        if isinstance(ids, (int,long)):
            ids = [ids]
        return self.pool.get('checklist.task.instance').search(cr, uid, [('checklist_task_id','in',ids)])

    _columns = {
        'checklist_task_id': fields.many2one('checklist.task', 'Checklist Task', required=True, ondelete='cascade'),
        'checklist_id': fields.related('checklist_task_id', 'checklist_id', type='many2one', relation='checklist', string='Checklist'),
        'model_id': fields.related('checklist_id', 'model_id', type='many2one', relation='ir.model', string='Model'),
        'name': fields.related('checklist_task_id', 'name', type='char', size=128, string='Name'),
        'mandatory': fields.related('checklist_task_id', 'mandatory', type='boolean', string='Mandatory', help='Required to make active object'),
        'res_id': fields.integer('Resource ID', select=True, required=True),
        'active': fields.function(_get_activity, method=True, type='boolean', string='Active', store=False, multi='activity'),
        'sequence': fields.function(_get_activity, method=True, type='integer', string='Priority', store={
            'checklist.task': (_get_checklist_task_instance_ids, ['sequence'], 10),
        }, multi='activity'),
        'field_ids_to_fill': fields.function(_get_activity, method=True, type='one2many', relation='checklist.task.field', string='Fields to fill', store=False, multi='activity'),
        'field_ids_filled': fields.function(_get_activity, method=True, type='one2many', relation='checklist.task.field', string='Filled fields', store=False, multi='activity'),
        'progress_rate': fields.float('Progress Rate', digits=(16, 2)),
    }

    _defaults = {
        'progress_rate': lambda *a: 0.0,
        'sequence': lambda *a: 15,
    }        
checklist_task_instance()

class checklist_exception(osv.osv):
    _name = 'checklist.exception'
    _description = 'Checklist Exception'
    _rec_name = 'checklist_task_id'
   
    _columns = {
        'checklist_id': fields.many2one('checklist', 'Checklist', select=True),
        'checklist_task_id': fields.many2one('checklist.task', 'Checklist Task', select=True),
        'exception_type': fields.selection([
            ('field', 'Field'),
            ('action', 'Action'),
             ], 'Type', select=True),
        'res_id': fields.integer('Resource'),
        'action_id': fields.many2one('ir.actions.server', 'Action', select=True),
        'field_id': fields.many2one('checklist.task.field', 'Field', select=True),
        'exception': fields.text('Exception'),
        'stack': fields.text('Stack Trace'),
        'create_date': fields.datetime('Creation Date'),
    }

    _order = "create_date desc"
checklist_exception()

native_orm_init = orm.orm.__init__
native_orm_create = orm.orm.create
native_orm_write = orm.orm.write
native_orm_fields_view_get = orm.orm_template.fields_view_get

def __init__object_and_checklist(self, cr):
    """Override __init__ method to update checklist cache"""
    result = native_orm_init(self, cr)
    checklist_pool = self.pool.get('checklist')
    if checklist_pool and hasattr(checklist_pool, '_update_models'):
        model_ids = self.pool.get('ir.model').search(cr, 1, [('model', '=', self._name)], limit=1)
        if model_ids:
            model_id = model_ids[0]
            models = {model_id: {'checklist_id': False, 'active_field': False}}
            checklist_ids = checklist_pool.search(cr, 1, [('model_id', '=', model_id)], limit=1)
            if checklist_ids:
                checklist = checklist_pool.read(cr, 1, checklist_ids[0])
                models[model_id] = {'checklist_id': checklist['id'], 'active_field': checklist['active_field']}
            checklist_pool._update_models(cr, models)
    return result

def create_object_and_checklist(self, cr, uid, vals, context=None):
    """Override create method to create checklist task instances if exist"""
    object_id = native_orm_create(self, cr, uid, vals, context)
    checklist_pool = self.pool.get('checklist')
    if object_id and checklist_pool and hasattr(checklist_pool, 'checklists_cache') and checklist_pool.checklists_cache.get(self._name, False):
        for checklist_task_id in self.pool.get('checklist.task').search(cr, uid, [('checklist_id', '=', checklist_pool.checklists_cache[self._name])]):
            self.pool.get('checklist.task.instance').create(cr, uid, {'checklist_task_id': checklist_task_id, 'res_id':object_id}, context=context)
        checklist_pool._compute_progress_rates(self, cr, uid, object_id)
    return object_id

def write_object_and_checklist(self, cr, uid, ids, vals, context=None):
    """Override create method to create checklist task instances if exist"""
    result = native_orm_write(self, cr, uid, ids, vals, context)
    checklist_pool = self.pool.get('checklist')
    if result and checklist_pool and hasattr(checklist_pool, 'checklists_cache') and checklist_pool.checklists_cache.get(self._name, False):
        checklist_pool._compute_progress_rates(self, cr, uid, ids)
    return result

def object_and_checklist_fields_view_get(self, cr, uid, view_id=None, view_type='form', context=None, toolbar=False):
    """Override fields_view_get method to add checklist task instances if exist"""
    fields_view = native_orm_fields_view_get(self, cr, uid, view_id, view_type, context, toolbar)
    checklist_pool = self.pool.get('checklist')
    if checklist_pool and hasattr(checklist_pool, 'checklists_cache') and checklist_pool.checklists_cache.get(self._name, False):
        checklist = checklist_pool.read(cr, uid, checklist_pool.checklists_cache[self._name], ['view_ids'])
        if not view_id:
            cr.execute("""SELECT id FROM ir_ui_view
                          WHERE model=%s AND type=%s AND inherit_id IS NULL
                          LIMIT 1""", (self._name, view_type))
            view_id = cr.fetchone()[0]
        if not checklist['view_ids'] or view_id in checklist['view_ids']:
            arch = fields_view['arch']
            arch_list = []
            fields_view['fields']['total_progress_rate'] = {'string': 'Progress Rate', 'type': 'float', 'context': {}}
            if view_type == 'tree':
                arch_list.append(arch[:arch.rfind('<')])
                arch_list.append("""<field name="total_progress_rate" readonly="1" widget="progressbar"/>""")
                arch_list.append(arch[arch.rfind('<'):])
                fields_view['arch'] = ''.join(arch_list)
            if view_type == 'form':
                arch_list.append(arch[:arch.find('>') + 1])
                arch_list.append('<group colspan="3" col="4">')
                arch_list.append(arch[arch.find('>') + 1:arch.rfind('<')])
                arch_list.append('</group>')
                arch_list.append('<group colspan="1">')
                arch_list.append("""
        <notebook>
            <page string="Checklist" col="2">
                <field name="total_progress_rate" readonly="1" widget="progressbar"/>
                <field name="checklist_task_instance_ids" nolabel="1" readonly="1" colspan="2" context="{'active_test': True}"/>
            </page>
        </notebook>
""")
                arch_list.append('</group>')
                arch_list.append(arch[arch.rfind('<'):])
                fields_view['fields']['checklist_task_instance_ids'] = {'string': 'Tasks', 'type': 'one2many', 'relation': 'checklist.task.instance', 'context': {}}
            fields_view['arch'] = ''.join(arch_list)
    return fields_view

orm.orm.__init__ = __init__object_and_checklist
orm.orm.create = create_object_and_checklist
orm.orm.write = write_object_and_checklist
orm.orm_template.fields_view_get = object_and_checklist_fields_view_get
