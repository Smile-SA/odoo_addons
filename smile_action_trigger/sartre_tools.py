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

from openerp import SUPERUSER_ID, tools
from openerp.osv import orm, osv


def _get_exception_message(exception):
    msg = isinstance(exception, (osv.except_osv, orm.except_orm)) and exception.value or exception
    return tools.ustr(msg)


def _get_browse_record_dict(obj, cr, uid, ids, fields_list=None, context=None):
    """Get a dictionary of dictionaries from browse records list"""
    if isinstance(ids, (int, long)):
        ids = [ids]
    if fields_list is None:
        fields_list = [f for f in obj._columns if obj._columns[f]._type != 'binary']
    browse_record_dict = {}
    for object_inst in obj.browse(cr, SUPERUSER_ID, ids, context):
        for field in fields_list:
            browse_record_dict.setdefault(object_inst.id, {})[field] = getattr(object_inst, field)
    return browse_record_dict


def _get_id_from_browse_record(value):
    if isinstance(value, orm.browse_record):
        value = value.id
    if isinstance(value, orm.browse_record_list):
        value = [v.id for v in value]
    return value
