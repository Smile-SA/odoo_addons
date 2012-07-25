# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2011-2012 Smile (<http: //www.smile.fr>).
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
#    along with this program.  If not, see <http: //www.gnu.org/licenses/>.
#
##############################################################################

from osv import orm
from osv.fields import property as property_column


def new_get_by_id(self, obj, cr, uid, prop_name, ids, context=None):
    prop = obj.pool.get('ir.property')
    vids = [obj._name + ', ' + str(oid) for oid in ids]

    # Change by Smile  #
    domain = prop._get_domain(cr, uid, prop_name, obj._name, context)
    ###################
    if vids:
        domain = [('res_id', 'in', vids)] + domain
    return prop.search(cr, uid, domain, context=context)


def new_fnct_write(self, obj, cr, uid, id_, prop_name, id_val, obj_dest, context=None):
    if context is None:
        context = {}

    def_id = self._field_get(cr, uid, obj._name, prop_name)
    company = obj.pool.get('res.company')
    cid = context.get('company_id', None)
    if not cid:
        cid = company._company_default_get(cr, uid, obj._name, def_id, context=context)
    context['force_company_id'] = cid

    nids = self._get_by_id(obj, cr, uid, [prop_name], [id_], context)
    if nids:
        cr.execute('DELETE FROM ir_property WHERE id IN %s', (tuple(nids), ))

    default_val = self._get_default(obj, cr, uid, prop_name, context)
    property_create = False
    if isinstance(default_val, orm.browse_record):
        if default_val.id != id_val:
            property_create = True
    elif default_val != id_val:
        property_create = True

    if property_create:
        propdef = obj.pool.get('ir.model.fields').browse(cr, uid, def_id, context=context)
        prop = obj.pool.get('ir.property')
        return prop.create(cr, uid, {
            'name': propdef.name,
            'value': id_val,
            'res_id': obj._name + ', ' + str(id_),
            'company_id': cid,
            'fields_id': def_id,
            'type': self._type,
        }, context=context)
    return False


def new_fnct_read(self, obj, cr, uid, ids, prop_name, obj_dest, context=None):
    context = context or {}

    if isinstance(ids, (int, long)):
        ids = [ids]

    default_val, replaces = self._get_defaults(obj, cr, uid, prop_name, context)
    res = {}
    for resource_id in ids:
        res[resource_id] = default_val.copy()

    properties = obj.pool.get('ir.property')
    global_domain = [('fields_id.model', '=', obj._name), ('fields_id.name', 'in', prop_name)]
    user_company_id = obj.pool.get('res.users').read(cr, uid, uid, ['company_id'], context, '_classic_write')['company_id']

    resources = map(lambda x: {'id': x}, ids)
    if 'company_id' in obj._columns:
        resources = obj.read(cr, uid, ids, ['company_id'], context, '_classic_write')
    for resource in resources:
        domain = global_domain[:]
        domain.extend(['|', ('res_id', '=', '%s, %s' % (obj._name, resource['id'])), ('res_id', '=', False)])
        company_id = context.get('company_id', False)
        if not company_id and 'company_id' in obj._columns:
            company_id = resource['company_id']
        if not company_id:
            company_id = user_company_id
        domain.extend(['|', ('company_id', '=', company_id), ('company_id', '=', False)])
        nids = properties.search(cr, uid, domain, context=context)
        for prop in properties.browse(cr, uid, nids, context):
            value = properties.get_by_record(cr, uid, prop, context=context)
            res[resource['id']][prop.fields_id.name] = value or False
            if value and (prop.type == 'many2one'):
                record_exists = obj.pool.get(value._name).exists(cr, uid, value.id)
                if record_exists:
                    replaces.setdefault(value._name, {})
                    replaces[value._name][value.id] = True
                else:
                    res[resource['id']][prop.fields_id.name] = False

    for rep in replaces:
        nids = obj.pool.get(rep).search(cr, uid, [('id', 'in', replaces[rep].keys())], context=context)
        replaces[rep] = dict(obj.pool.get(rep).name_get(cr, uid, nids, context=context))

    for prop in prop_name:
        for id_ in ids:
            if res[id_][prop] and hasattr(res[id_][prop], '_name'):
                res[id_][prop] = (res[id_][prop].id, replaces[res[id_][prop]._name].get(res[id_][prop].id, False))

    return res

property_column._get_by_id = new_get_by_id
property_column._fnct_write = new_fnct_write
property_column._fnct_read = new_fnct_read
