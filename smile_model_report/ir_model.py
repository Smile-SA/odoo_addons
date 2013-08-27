# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2004-2009 Tiny SPRL (<http://tiny.be>).
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

from osv import fields, orm
from modules.registry import Registry
from tools.func import wraps


def cache_restarter(original_method):
    @wraps(original_method)
    def wrapper(self, cr, module):
        return original_method(self, cr, module)
    return wrapper


class IrModelFields(orm.Model):
    _inherit = 'ir.model.fields'
    _order = 'sequence, id'

    def __init__(self, pool, cr):
        super(IrModelFields, self).__init__(pool, cr)
        setattr(Registry, 'load', cache_restarter(getattr(Registry, 'load')))

    def _get_display_in_report(self, cr, uid, ids, name, args, context=None):
        res = {}.fromkeys(ids, True)
        for field in self.browse(cr, uid, ids, context):
            if field.ttype in ('one2many', 'serialized'):
                res[field.id] = False
                continue
            model_id = field.model_id
            model_obj = self.pool.get(model_id.model)
            if not model_obj:
                continue
            if field.name not in model_obj._columns:
                continue
            data = model_obj._columns[field.name]
            if isinstance(data, (fields.property, fields.dummy, fields.related)):
                res[field.id] = False
            elif isinstance(data, fields.function):
                if not data.store or not data._fnct_inv:
                    res[field.id] = False
        return res

    def _set_display_in_report(self, cr, uid, ids, name, value, arg, contex=None):
        for field_id in ids:
            cr.execute('UPDATE ir_model_fields SET display_in_report=%s Where id = %s', (value, field_id))
        return True

    _columns = {
        'sequence': fields.integer("Sequence"),
        'info': fields.text('Information', translate=True),
        'display_in_report': fields.function(_get_display_in_report, fnct_inv=_set_display_in_report, type='boolean', store=True,
                                             string='Display in report', required=True),
    }

    _defaults = {
        'sequence': 5,
    }
