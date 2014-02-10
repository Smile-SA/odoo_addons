# -*- encoding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2013 Smile (<http://www.smile.fr>). All Rights Reserved
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

from openerp import sql_db
from openerp.service import security, web_services
from openerp.service.web_services import common, db


def get_duplicated_indexes(self, name):
    db = sql_db.db_connect(name)
    cr = db.cursor()
    cr.execute("SELECT 0 FROM pg_proc WHERE proname = 'array_accum' AND proisagg;")
    if not cr.rowcount:
        cr.execute("CREATE AGGREGATE array_accum (anyelement) (sfunc = array_append, stype = anyarray, initcond = '{}');")
    cr.execute("""SELECT indrelid::regclass as table, array_accum(indexrelid::regclass) as duplicated_indexes
FROM pg_index GROUP BY indrelid, indkey HAVING count(*) > 1;""")
    return cr.dictfetchall()


def get_missing_indexes(self, name):
    db = sql_db.db_connect(name)
    cr = db.cursor()
    cr.execute("""SELECT relname as table,
seq_scan-idx_scan as too_much_seq,
case when seq_scan-idx_scan>0 THEN 'Missing Index?' ELSE 'OK' END as index,
pg_relation_size(relname::regclass) as table_size,
seq_scan, idx_scan
FROM pg_stat_all_tables
WHERE schemaname='public' AND pg_relation_size(relname::regclass)>80000
ORDER BY too_much_seq DESC;""")
    return cr.dictfetchall()


def get_unused_indexes(self, name):
    db = sql_db.db_connect(name)
    cr = db.cursor()
    cr.execute("""SELECT relid::regclass as table, indexrelid::regclass as unused_index
FROM pg_stat_user_indexes JOIN pg_index USING (indexrelid)
WHERE idx_scan = 0 AND indisunique IS FALSE AND pg_relation_size(relid::regclass) > 0;""")
    return cr.dictfetchall()


native_db_dispatch = db.dispatch


def new_db_dispatch(self, method, params):
    if method in ['get_missing_indexes', 'get_unused_indexes', 'get_duplicated_indexes']:
        passwd = params[0]
        params = params[1:]
        security.check_super(passwd)
        return getattr(self, method)(*params)
    return native_db_dispatch(self, method, params)


db.dispatch = new_db_dispatch
db.get_duplicated_indexes = get_duplicated_indexes
db.get_missing_indexes = get_missing_indexes
db.get_unused_indexes = get_unused_indexes


def get_running_requests(self):
    return web_services._requests


native_common_dispatch = common.dispatch


def new_common_dispatch(self, method, params):
    if method in ['get_running_requests']:
        passwd = params[0]
        params = params[1:]
        security.check_super(passwd)
        return getattr(self, method)(*params)
    return native_common_dispatch(self, method, params)


common.dispatch = new_common_dispatch
common.get_running_requests = get_running_requests
