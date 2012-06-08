# -*- coding: utf-8 -*-
##############################################################################
#    
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2011-2012 Smile (<http://www.smile.fr>).
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.     
#
##############################################################################

import inspect
import logging
import time

from osv import osv, fields
import tools
from tools.func import wraps
from tools.safe_eval import safe_eval as eval

def _get_exception_message(exception):
    msg = isinstance(exception, osv.except_osv) and exception.value or exception
    return tools.ustr(msg)

def check_if_is_not_decorated(method):
    while method.func_closure:
        if method.__name__ == 'delegate_method':
            return False
        method = method.func_closure[0].cell_contents
    return True

def launch_delegation_decorations(original_method):
    @wraps(original_method)
    def wrapper(self, cr, mode):
        res = original_method(self, cr, mode)
        if isinstance(self, osv.osv_pool):
            delegation_tmpl_obj = self.get('delegation.template')
            if delegation_tmpl_obj and hasattr(delegation_tmpl_obj, 'decorate_delegated_methods'):
                delegation_tmpl_obj.decorate_delegated_methods(cr)
        return res
    return wrapper

class DelegationTemplate(osv.osv):
    _name = 'delegation.template'
    _description = 'Delegation Template'

    def _get_method_argument_names(self, cr, uid, ids, name, args, context=None):
        res = {}.fromkeys(ids, '')
        for delegation in self.browse(cr, uid, ids, context):
            res[delegation.id] = self.pool.get('ir.model.methods').get_method_args(cr, uid, delegation.method_id.id, context)
        return res

    _columns = {
        'name': fields.char('Name', size=64, required=True),
        'active': fields.boolean('Active'),
        'model_id': fields.many2one('ir.model', 'Model', required=True, ondelete='cascade'),
        'model': fields.related('model_id', 'model', type='char', size=64, string='Model', readonly=True, store=True),
        'method_id': fields.many2one('ir.model.methods', 'Method', required=True, ondelete='cascade'),
        'method': fields.related('method_id', 'name', type='char', size=64, string='Method', readonly=True, store=True),
        'method_args': fields.function(_get_method_argument_names, method=True, type='char', string='Arguments'),
        'domain': fields.text('Domain', help=""),
        'user_field_id': fields.many2one('ir.model.fields', 'User field', help="To save delegate user in object"),
        'client_action_id': fields.many2one('ir.values', 'Client Action'),
    }

    _defaults = {
        'active': True,
    }

    def onchange_model_or_method(self, cr, uid, ids, model_id, method_id, context=None):
        res = {'value': {}}
        if model_id:
            self.pool.get('ir.model').update_methods_list(cr, uid, model_id, context)
            if method_id:
                method_model_id = self.pool.get('ir.model.methods').read(cr, uid, method_id, ['model_id'], context, '_classic_write')['model_id']
                if model_id != method_model_id:
                    res['value'].update({'method_id': False, 'method_args': ''})
                else:
                    res['value']['method_args'] = self.pool.get('ir.model.methods').get_method_args(cr, uid, method_id, context)
            else:
                res['value']['method_args'] = ''
        return res

    def check_domain(self, cr, uid, delegation_tmpl_id, kwargs, context=None):
        assert isinstance(delegation_tmpl_id, (int, long)), 'delegation_tmpl_id must be an integer'
        delegation_tmpl = self.browse(cr, 1, delegation_tmpl_id, context)
        if not delegation_tmpl.domain:
            return True
        localdict = kwargs.copy()
        localdict.update({
            'objects': kwargs.get('ids') and self.pool.get(delegation_tmpl.model).browse(cr, uid, kwargs['ids'], context) or [],
            'time': time,
        })
        try:
            return eval(delegation_tmpl.domain, localdict)
        except Exception, e:
            logging.getLogger('smile_delegation').error("Domain evaluation failed: %s - %s" % (delegation_tmpl.name, _get_exception_message(e)))
            return False

    def decorate_delegated_methods(self, cr):
        delegation_tmpl_ids = self.search(cr, 1, [], context={'active_test': True})
        methods_to_decorate = [(delegation_tmpl.model, delegation_tmpl.method) for delegation_tmpl in self.browse(cr, 1, delegation_tmpl_ids)]
        for model, method_name in list(set(methods_to_decorate)):
            model_class = self.pool.get(model).__class__
            method = getattr(model_class, method_name)
            if check_if_is_not_decorated(method):
                setattr(model_class, method_name, delegation_decorator(method))
        return True

    def __init__(self, pool, cr):
        super(DelegationTemplate, self).__init__(pool, cr)
        setattr(osv.osv_pool, 'init_set', launch_delegation_decorations(getattr(osv.osv_pool, 'init_set')))

    def create(self, cr, uid, vals, context=None):
        res_id = super(DelegationTemplate, self).create(cr, uid, vals, context)
        self.decorate_delegated_methods(cr)
        return res_id

    def write(self, cr, uid, ids, vals, context=None):
        res = super(DelegationTemplate, self).write(cr, uid, ids, vals, context)
        self.decorate_delegated_methods(cr)
        return res

    def unlink(self, cr, uid, ids, context=None):
        res = super(DelegationTemplate, self).unlink(cr, uid, ids, context)
        self.decorate_delegated_methods(cr)
        return res

    def create_client_action(self, cr, uid, ids, context=None):
        if isinstance(ids, (int, long)):
            ids = [ids]
        for delegation_tmpl in self.browse(cr, uid, ids, context):
            if not delegation_tmpl.client_action_id:
                act_window_vals = {
                    'name': delegation_tmpl.name,
                    'type': 'ir.actions.act_window',
                    'domain': [('model', '=', delegation_tmpl.model)],
                    'context': context,
                    'res_model': 'delegation.delegation',
                    'src_model': delegation_tmpl.model,
                    'view_type': 'form',
                    'view_mode': 'tree,form',
                    'target': 'new',
                }
                act_window_id = self.pool.get('ir.actions.act_window').create(cr, uid, act_window_vals, context)
                ir_value_vals = {
                    'name': delegation_tmpl.name,
                    'object': True,
                    'model_id': delegation_tmpl.model_id.id,
                    'model': delegation_tmpl.model_id.model,
                    'key2': 'client_action_multi',
                    'value': 'ir.actions.act_window,%d' % act_window_id,
                }
                client_action_id = self.pool.get('ir.values').create(cr, uid, ir_value_vals, context)
                delegation_tmpl.write({'client_action_id': client_action_id})
        return True
DelegationTemplate()

class Delegation(osv.osv):
    _name = 'delegation.delegation'
    _description = 'Delegation'
    _rec_name = 'delegation_tmpl_id'
    _order = 'delegation_tmpl_id'

    _columns = {
        'delegation_tmpl_id': fields.many2one('delegation.template', 'Delegation Template', required=True, ondelete='restrict'),
        'model': fields.related('delegation_tmpl_id', 'model_id', 'model', type='char', size=64, string='Model', readonly=True, store=True),
        'method': fields.related('delegation_tmpl_id', 'method_id', 'name', type='char', size=64, string='Method', readonly=True, store=True),
        'active': fields.boolean('Active'),
        'date_start': fields.date('Start Date'),
        'date_stop': fields.date('End Date'),
        'user_id': fields.many2one('res.users', 'Delegator', required=True, ondelete='cascade'),
        'delegate_ids': fields.many2many('res.users', 'delegation_users_rel', 'delegation_id', 'delegate_id', 'Delegates'),
        'history_ids': fields.one2many('delegation.history', 'delegation_id', 'History', readonly=True),
    }

    _defaults = {
        'active': True,
        'user_id': lambda self, cr, uid, context = None: uid,
    }

    @tools.cache(skiparg=3)
    def get_delegator_id(self, cr, uid, delegation_id):
        assert isinstance(delegation_id, (int, long)), 'delegation_id must be an integer'
        return self.read(cr, 1, delegation_id, ['user_id'], load='_classic_write')['user_id']

    @tools.cache()
    def get_delegation_ids(self, cr, uid, model, method):
        today = time.strftime('%Y-%m-%d')
        return self.search(cr, 1, [
                ('model', '=', model),
                ('method', '=', method),
                ('delegate_ids', 'in', uid),
                '|', ('date_start', '=', False), ('date_start', '<=', today),
                '|', ('date_end', '=', False), ('date_end', '>=', today),
            ], context={'active_test': True})

    def cache_restart(self, cr):
        self.get_delegation_ids.clear_cache(cr.dbname)
        self.get_delegator_id.clear_cache(cr.dbname)

    def create(self, cr, uid, vals, context=None):
        res_id = super(Delegation, self).create(cr, uid, vals, context)
        self.cache_restart(cr)
        return res_id

    def write(self, cr, uid, ids, vals, context=None):
        res = super(Delegation, self).write(cr, uid, ids, vals, context)
        self.cache_restart(cr)
        return res

    def unlink(self, cr, uid, ids, context=None):
        res = super(Delegation, self).unlink(cr, uid, ids, context)
        self.cache_restart(cr)
        return res

    def historize(self, cr, uid, delegation_id, delegate_id, kwargs, context=None):
        assert isinstance(delegation_id, (int, long)), 'delegation_id must be an integer'
        assert isinstance(delegate_id, (int, long)), 'delegate_id must be an integer'
        return self.pool.get('delegation.history').create(cr, 1, {
            'delegation_id': delegation_id,
            'delegate_id': delegate_id,
            'method_args': repr(kwargs),
        }, context)
Delegation()

class DelegationHistory(osv.osv):
    _name = 'delegation.history'
    _description = 'Delegation History'
    _rec_name = 'delegation_id'
    _order = 'create_date desc'

    _columns = {
        'delegation_id': fields.many2one('delegation.delegation', 'Delegation', required=True, ondelete='restrict', readonly=True),
        'delegate_id': fields.many2one('res.users', 'Delegate', required=True, ondelete='restrict', readonly=True),
        'create_date': fields.datetime('Date', required=True, readonly=True),
        'method_args': fields.text('Method Arguments', required=True, readonly=True),
    }
DelegationHistory()

def _get_kwargs(method, args, kwargs):
    kwargs = kwargs or {}
    argument_names = inspect.getargspec(method)[0]
    kwargs.update({}.fromkeys(argument_names, False))
    for index, arg in enumerate(argument_names):
        if index < len(args):
            kwargs[arg] = args[index]
    if 'context' in kwargs and not isinstance(kwargs['context'], dict):
        kwargs['context'] = {}
    return kwargs

def _get_openerp_classic_args(kwargs):
    obj = kwargs.get('self') or kwargs.get('obj')
    cr = kwargs.get('cr') or kwargs.get('cursor')
    uid = kwargs.get('uid') or kwargs.get('user')
    ids = kwargs.get('ids') or kwargs.get('id')
    return obj, cr, uid, ids, kwargs.get('context', {})

def _udpate_user_field(obj, method, cr, uid, ids, vals, context, kwargs):
    method = kwargs['method']
    if method in ('create', 'write'):
        if 'vals' in kwargs:
            kwargs['vals'].update(vals)
        else:
            logging.getLogger('smile_delegation').warning("vals not found in %s,%s" % (obj._name, method))
    elif ids and method != 'unlink':
        obj.write(cr, uid, ids, vals, context)

def delegate(kwargs):
    obj, cr, uid, ids, context = _get_openerp_classic_args(kwargs)
    method = kwargs['method']
    delegation_obj = obj.pool.get('delegation.delegation')
    delegation_tmpl_obj = obj.pool.get('delegation.template')
    delegation_ids = delegation_obj.get_delegation_ids(cr, uid, obj._name, method)
    for delegation in delegation_obj.browse(cr, uid, delegation_ids, context):
        delegation_tmpl = delegation.delegation_tmpl_id
        if delegation_tmpl_obj.check_domain(cr, uid, delegation_tmpl.id, kwargs, context=context):
            delegation_obj.historize(cr, uid, delegation.id, uid, kwargs, context=context)
            if delegation_tmpl.user_field_id:
                _udpate_user_field(obj, cr, uid, ids, {delegation_tmpl.user_field_id.name: uid}, context, kwargs)
            kwargs['uid' in kwargs and 'uid' or 'user'] = delegation_obj.get_delegator_id(cr, uid, delegation.id)
            break
    return kwargs

def delegation_decorator(original_method):
    def delegate_method(*args, **kwargs):
        kwargs = _get_kwargs(original_method, args, kwargs)
        kwargs['method'] = original_method.__name__
        new_kwargs = delegate(kwargs)
        obj = new_kwargs['self']
        for kw in ('self', 'method'):
            if kw in new_kwargs:
                del new_kwargs[kw]
        return original_method(obj, **new_kwargs)
    return delegate_method
