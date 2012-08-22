# -*- encoding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2011 Smile (<http://www.smile.fr>). All Rights Reserved
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


import netsvc
from osv import orm, fields
from tools.safe_eval import safe_eval as eval


def get_pg_type(f):
    '''Override the original method in order to accept fields.serialized'''
    type_dict = {
        fields.boolean: 'bool',
        fields.integer: 'int4',
        fields.integer_big: 'int8',
        fields.text: 'text',
        fields.date: 'date',
        fields.time: 'time',
        fields.datetime: 'timestamp',
        fields.binary: 'bytea',
        fields.many2one: 'int4',
    }
    if type(f) in type_dict:
        f_type = (type_dict[type(f)], type_dict[type(f)])
    elif isinstance(f, fields.float):
        if f.digits:
            f_type = ('numeric', 'NUMERIC')
        else:
            f_type = ('float8', 'DOUBLE PRECISION')
    elif isinstance(f, (fields.char, fields.reference)):
        f_type = ('varchar', 'VARCHAR(%d)' % (f.size,))
    elif isinstance(f, fields.selection):
        if isinstance(f.selection, list) and isinstance(f.selection[0][0], (str, unicode)):
            f_size = reduce(lambda x, y: max(x, len(y[0])), f.selection, f.size or 16)
        elif isinstance(f.selection, list) and isinstance(f.selection[0][0], int):
            f_size = -1
        else:
            f_size = getattr(f, 'size', None) or 16

        if f_size == -1:
            f_type = ('int4', 'INTEGER')
        else:
            f_type = ('varchar', 'VARCHAR(%d)' % f_size)
    elif isinstance(f, (fields.function, fields.serialized)) and eval('fields.' + (f._type), globals()) in type_dict:
        t = eval('fields.' + (f._type), globals())
        f_type = (type_dict[t], type_dict[t])
    elif isinstance(f, (fields.function, fields.serialized)) and f._type == 'float':
        if f.digits:
            f_type = ('numeric', 'NUMERIC')
        else:
            f_type = ('float8', 'DOUBLE PRECISION')
    elif isinstance(f, (fields.function, fields.serialized)) and f._type == 'selection':
        f_type = ('text', 'text')
    elif isinstance(f, (fields.function, fields.serialized)) and f._type == 'char':
        f_type = ('varchar', 'VARCHAR(%d)' % (f.size))
    else:
        logger = netsvc.Logger()
        logger.notifyChannel("init", netsvc.LOG_WARNING, '%s type not supported!' % (type(f)))
        f_type = None
    return f_type

orm.get_pg_type = get_pg_type
