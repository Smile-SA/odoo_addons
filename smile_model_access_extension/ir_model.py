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
from operator import __and__


def ir_model_fields_access_decorator(fnct):
    def new_fnct(self, cr, *args, **kwds):
        result = getattr(osv.osv, fnct.__name__)(self, cr, *args, **kwds)
        if result:
            self._update_model_fields_access_cache(cr)
        return result
    return new_fnct


class ir_model_fields_access(osv.osv):
    _name = 'ir.model.fields.access'

    _columns = {
        'name': fields.char('Name', size=64, required=True, select=True),
        'model_id': fields.many2one('ir.model', 'Object', required=True, domain=[('osv_memory', '=', False)], select=True),
        'group_id': fields.many2one('res.groups', 'Group', ondelete='cascade'),
        'states': fields.char('States', size=64),
        'field_id': fields.many2one('ir.model.fields', 'Field'),
        'perm_write': fields.boolean('Write Access'),
    }

    # Cache = {model: {group_id: {field_name: {state: {'readonly': bool}}}}}
    def _update_model_fields_access_cache(self, cr):
        self.model_fields_access_cache = {}
        model_fields_access_ids = self.search(cr, 1, [])
        if model_fields_access_ids:
            for model_fields_access in self.browse(cr, 1, model_fields_access_ids):
                model = model_fields_access.model_id.model
                field_name = model_fields_access.field_id and model_fields_access.field_id.name or 'all_fields'
                group_id = model_fields_access.group_id and model_fields_access.group_id.id or 0
                self.model_fields_access_cache.setdefault(model, {}).setdefault(group_id, {}).setdefault(field_name, {})
                states = model_fields_access.states and model_fields_access.states.replace(' ', '').split(', ') \
                    or (self.pool.get(model)._columns.get('state', False) and dict(self.pool.get(model)._columns['state'].selection).keys()) \
                    or 'none'
                for state in states:
                    state_perms = self.model_fields_access_cache[model][group_id][field_name].setdefault(state, {})
                    state_perms['readonly'] = __and__(not model_fields_access.perm_write, state_perms.get('readonly', True))
                    self.model_fields_access_cache[model][group_id][field_name][state] = state_perms
        return True

    def __init__(self, pool, cr):
        super(ir_model_fields_access, self).__init__(pool, cr)
        cr.execute("SELECT * FROM pg_class WHERE relname=%s", (self._table, ))
        if cr.rowcount:
            self._update_model_fields_access_cache(cr)

    @ir_model_fields_access_decorator
    def create(self, cr, uid, vals, context=None):
        return super(ir_model_fields_access, self).create(cr, uid, vals, context)

    @ir_model_fields_access_decorator
    def write(self, cr, uid, ids, vals, context=None):
        return super(ir_model_fields_access, self).write(cr, uid, ids, vals, context)

    @ir_model_fields_access_decorator
    def unlink(self, cr, uid, ids, context=None):
        return super(ir_model_fields_access, self).unlink(cr, uid, ids, context)
ir_model_fields_access()

native_orm_fields_get = orm.orm_template.fields_get


def ir_model_fields_access_fields_get(self, cr, uid, allfields=None, context=None, write_access=True):
    res = native_orm_fields_get(self, cr, uid, allfields, context, write_access)
    if uid != 1 and hasattr(self.pool.get('ir.model.fields.access'), 'model_fields_access_cache'):
        cache = self.pool.get('ir.model.fields.access').model_fields_access_cache
        model = self._name
        if model in cache:
            user_group_ids = self.pool.get('res.users').read(cr, uid, uid, ['groups_id'])['groups_id']
            user_group_ids_in_cache = [group_id for group_id in user_group_ids if group_id in cache[model]]
            if not user_group_ids_in_cache and 0 in cache[model]:
                user_group_ids_in_cache = [0]
            if user_group_ids_in_cache:
                states = no_states = {}
                for group_id in user_group_ids_in_cache:
                    field_names = cache[model][group_id].keys()
                    for field_name in field_names:
                        for state in cache[model][group_id][field_name]:
                            state_perms = states.setdefault(field_name, {}).setdefault(state, {})
                            state_perms['readonly'] = __and__(cache[model][group_id][field_name][state]['readonly'], state_perms.get('readonly', True))
                            if state != 'none':
                                states[field_name][state] = state_perms
                            else:
                                no_states[field_name] = state_perms
                for field in res:
                    if field in states:
                        res[field]['states'] = dict([(state, states[field][state].items()) for state in states[field]])
                    elif states.get('all_fields', False):
                        res[field]['states'] = dict([(state, states['all_fields'][state].items()) for state in states['all_fields']])
                    if field in no_states:
                        res[field]['readonly'] = no_states[field]
                    elif no_states.get('all_fields', False):
                        res[field]['readonly'] = no_states['all_fields']
    return res

orm.orm_template.fields_get = ir_model_fields_access_fields_get
