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

import datetime
import time

from osv import orm


def new_store_set_values(self, cr, uid, ids, fields, context):
    """Calls the fields.function's "implementation function" for all ``fields``, on records with ``ids`` (taking care of
       respecting ``multi`` attributes), and stores the resulting values in the database directly."""
    if not ids:
        return True
    field_flag = False
    field_dict = {}
    if self._log_access:
        cr.execute('select id, write_date from ' + self._table + ' where id IN %s', (tuple(ids), ))
        res = cr.fetchall()
        for r in res:
            if r[1]:
                field_dict.setdefault(r[0], [])
                res_date = time.strptime((r[1])[: 19], '%Y-%m-%d %H:%M:%S')
                write_date = datetime.datetime.fromtimestamp(time.mktime(res_date))
                for i in self.pool._store_function.get(self._name, []):
                    if i[5]:
                        up_write_date = write_date + datetime.timedelta(hours=i[5])
                        if datetime.datetime.now() < up_write_date:
                            if i[1] in fields:
                                field_dict[r[0]].append(i[1])
                                if not field_flag:
                                    field_flag = True
    todo = {}
    keys = []
    for f in fields:
        if self._columns[f]._multi not in keys:
            keys.append(self._columns[f]._multi)
        todo.setdefault(self._columns[f]._multi, [])
        todo[self._columns[f]._multi].append(f)
    for key in keys:
        val = todo[key]
        if key:
            # uid == 1 for accessing objects having rules defined on store fields
            result = self._columns[val[0]].get(cr, self, ids, val, 1, context=context)
            for id_, value in result.items():
                if field_flag:
                    for f in value.keys():
                        if f in field_dict[id_]:
                            value.pop(f)
                upd0 = []
                upd1 = []
                for v in value:
                    if v not in val:
                        continue
                    # Modified by Smile  #
                    if val[0] in ('many2one', 'one2one') and self._columns[v]._type in ('many2one', 'one2one'):
                    #####################
                        try:
                            value[v] = value[v][0]
                        except (IndexError, KeyError):
                            pass
                    upd0.append('"' + v + '"=' + self._columns[v]._symbol_set[0])
                    upd1.append(self._columns[v]._symbol_set[1](value[v]))
                upd1.append(id_)
                if upd0 and upd1:
                    cr.execute('update "' + self._table + '" set ' + ', '.join(upd0) + ' where id = %s', upd1)

        else:
            for f in val:
                # uid == 1 for accessing objects having rules defined on store fields
                result = self._columns[f].get(cr, self, ids, f, 1, context=context)
                for r in result.keys():
                    if field_flag:
                        if r in field_dict.keys():
                            if f in field_dict[r]:
                                result.pop(r)
                for id_, value in result.items():
                    if self._columns[f]._type in ('many2one', 'one2one'):
                        try:
                            value = value[0]
                        except Exception:
                            pass
                    cr.execute('update "' + self._table + '" set ' + '"' + f + '"=' +
                               self._columns[f]._symbol_set[0] + ' where id = %s', (self._columns[f]._symbol_set[1](value), id_))
    return True

orm.orm._store_set_values = new_store_set_values
