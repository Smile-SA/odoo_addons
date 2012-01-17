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

from osv.fields import property as property_column

def new_fnct_read(self, obj, cr, uid, ids, prop_name, obj_dest, context=None):
    """Overriding by Smile to manage multi-company application"""

    default_val, replaces = self._get_defaults(obj, cr, uid, prop_name, context)
    res = {}
    for resource_id in ids:
        res[resource_id] = default_val.copy()

    properties = obj.pool.get('ir.property')
    global_domain = [('fields_id.model', '=', obj._name), ('fields_id.name', 'in', prop_name)]
    for resource in obj.read(cr, uid, ids, ['company_id'], context, '_classic_write'):
        domain = global_domain[:]
        domain.append(('res_id', '=', '%s,%s' % (obj._name, resource['id'])))
        if 'company_id' in obj._columns:
            domain += ['|', ('company_id', '=', resource['company_id']), ('company_id', '=', False)]
        nids = properties.search(cr, uid, domain, context=context)
        for prop in properties.browse(cr, uid, nids, context):
            value = properties.get_by_record(cr, uid, prop, context=context)
            res[prop.res_id.id][prop.fields_id.name] = value or False
            if value and (prop.type == 'many2one'):
                record_exists = obj.pool.get(value._name).exists(cr, uid, value.id)
                if record_exists:
                    replaces.setdefault(value._name, {})
                    replaces[value._name][value.id] = True
                else:
                    res[prop.res_id.id][prop.fields_id.name] = False

    for rep in replaces:
        nids = obj.pool.get(rep).search(cr, uid, [('id', 'in', replaces[rep].keys())], context=context)
        replaces[rep] = dict(obj.pool.get(rep).name_get(cr, uid, nids, context=context))

    for prop in prop_name:
        for id_ in ids:
            if res[id_][prop] and hasattr(res[id_][prop], '_name'):
                res[id_][prop] = (res[id_][prop].id , replaces[res[id_][prop]._name].get(res[id_][prop].id, False))

    return res

property_column._fnct_read = new_fnct_read
