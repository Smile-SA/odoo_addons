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

import logging
import time
import uuid

from openerp import service, sql_db
from openerp.tools import config, misc
from openerp.service import common, db, model, report

_logger = logging.getLogger('openerp.smile_detective')
service._requests = {}
_requests = service._requests


def smile_detective(min_delay):  # min_delay in seconds
    def detective_log(dispatch_func):
        def detective_dispatch(method, params):
            pid = uuid.uuid4()
            db, uid = params[0:2]
            param_str = repr(params[3:])
            start = time.time()
            _requests[pid] = (db, uid, method, param_str, start)
            try:
                result = dispatch_func(method, params)
            finally:
                del _requests[pid]
            delay = time.time() - start
            if delay > min_delay:
                msg = u"WS_DB:%s WS_UID:%s WS_METHOD:%s WS_PARAMS:%s WS_TIMER:%s" % (db, uid, method, param_str, delay * 1000.0,)
                # WS_TIMER in milliseconds
                _logger.info(msg)
            return result
        return detective_dispatch
    return detective_log


model.dispatch = smile_detective(config.get('log_service_object', 0.500))(model.dispatch)
report.dispatch = smile_detective(config.get('log_service_report', 0.500))(report.dispatch)

native_dumpstacks = misc.dumpstacks


def smile_dumpstacks(sig, frame):
    _logger.info("\n".join(map(str, _requests.values())))
    native_dumpstacks(sig, frame)

misc.dumpstacks = smile_dumpstacks


def get_current_locks(dbname):
    db = sql_db.db_connect(dbname)
    cr = db.cursor()
    cr.execute("SHOW server_version;")
    version = cr.fetchone()[0]
    if version >= '9.2':
        query = """
            select
            wait_act.datname,
            wait_act.usename,
            waiter.pid as wpid,
            holder.pid as hpid,
            waiter.locktype as type,
            waiter.transactionid as xid,
            waiter.virtualtransaction as wvxid,
            holder.virtualtransaction as hvxid,
            waiter.mode as wmode,
            holder.mode as hmode,
            wait_act.state as wstate,
            hold_act.state as hstate,
            pg_class.relname,
            substr(wait_act.query,1,30) as wquery,
            substr(hold_act.query,1,30) as hquery,
            age(now(),wait_act.query_start) as wdur,
            age(now(),hold_act.query_start) as hdur
            from pg_locks holder join pg_locks waiter on (
            holder.locktype = waiter.locktype and (
            holder.database, holder.relation,
            holder.page, holder.tuple,
            holder.virtualxid,
            holder.transactionid, holder.classid,
            holder.objid, holder.objsubid
            ) is not distinct from (
            waiter.database, waiter.relation,
            waiter.page, waiter.tuple,
            waiter.virtualxid,
            waiter.transactionid, waiter.classid,
            waiter.objid, waiter.objsubid
            ))
            join pg_stat_activity hold_act on (holder.pid=hold_act.pid)
            join pg_stat_activity wait_act on (waiter.pid=wait_act.pid)
            left join pg_class on (holder.relation = pg_class.oid)
            where holder.granted and not waiter.granted
            order by wdur desc;
        """
    else:
        query = """
            select
            wait_act.datname,
            pg_class.relname,
            wait_act.usename,
            waiter.pid as waiterpid,
            waiter.locktype,
            waiter.transactionid as xid,
            waiter.virtualtransaction as wvxid,
            waiter.mode as wmode,
            wait_act.waiting as wwait,
            substr(wait_act.current_query,1,30) as wquery,
            age(now(),wait_act.query_start) as wdur,
            holder.pid as holderpid,
            holder.mode as hmode,
            holder.virtualtransaction as hvxid,
            hold_act.waiting as hwait,
            substr(hold_act.current_query,1,30) as hquery,
            age(now(),hold_act.query_start) as hdur
            from pg_locks holder join pg_locks waiter on (
            holder.locktype = waiter.locktype and (
            holder.database, holder.relation,
            holder.page, holder.tuple,
            holder.virtualxid,
            holder.transactionid, holder.classid,
            holder.objid, holder.objsubid
            ) is not distinct from (
            waiter.database, waiter.relation,
            waiter.page, waiter.tuple,
            waiter.virtualxid,
            waiter.transactionid, waiter.classid,
            waiter.objid, waiter.objsubid
            ))
            join pg_stat_activity hold_act on (holder.pid=hold_act.procpid)
            join pg_stat_activity wait_act on (waiter.pid=wait_act.procpid)
            left join pg_class on (holder.relation = pg_class.oid)
            where holder.granted and not waiter.granted
            order by wdur desc;"""
    cr.execute(query)
    result = cr.dictfetchall()
    cr.close()
    return result


def get_duplicated_indexes(dbname):
    db = sql_db.db_connect(dbname)
    cr = db.cursor()
    cr.execute("SELECT 0 FROM pg_proc WHERE proname = 'array_accum' AND proisagg;")
    if not cr.rowcount:
        cr.execute("CREATE AGGREGATE array_accum (anyelement) (sfunc = array_append, stype = anyarray, initcond = '{}');")
    cr.execute("""SELECT indrelid::regclass as table, array_accum(indexrelid::regclass) as duplicated_indexes
FROM pg_index GROUP BY indrelid, indkey HAVING count(*) > 1;""")
    result = cr.dictfetchall()
    cr.close()
    return result


def get_missing_indexes(dbname):
    db = sql_db.db_connect(dbname)
    cr = db.cursor()
    cr.execute("""SELECT relname as table,
seq_scan-idx_scan as too_much_seq,
case when seq_scan-idx_scan>0 THEN 'Missing Index?' ELSE 'OK' END as index,
pg_relation_size(relname::regclass) as table_size,
seq_scan, idx_scan
FROM pg_stat_all_tables
WHERE schemaname='public' AND pg_relation_size(relname::regclass)>80000
ORDER BY too_much_seq DESC;""")
    result = cr.dictfetchall()
    cr.close()
    return result


def get_unused_indexes(dbname):
    db = sql_db.db_connect(dbname)
    cr = db.cursor()
    cr.execute("""SELECT relid::regclass as table, indexrelid::regclass as unused_index
FROM pg_stat_user_indexes JOIN pg_index USING (indexrelid)
WHERE idx_scan = 0 AND indisunique IS FALSE AND pg_relation_size(relid::regclass) > 0;""")
    result = cr.dictfetchall()
    cr.close()
    return result


native_db_dispatch = db.dispatch


def new_db_dispatch(method, params):
    if method in ['get_missing_indexes', 'get_unused_indexes',
                  'get_duplicated_indexes', 'get_current_locks']:
        passwd = params[0]
        params = params[1:]
        service.security.check_super(passwd)
        return globals()[method](*params)
    return native_db_dispatch(method, params)


db.dispatch = new_db_dispatch
db.get_duplicated_indexes = get_duplicated_indexes
db.get_missing_indexes = get_missing_indexes
db.get_unused_indexes = get_unused_indexes


def get_running_requests(self):
    return service._requests


native_common_dispatch = common.dispatch


def new_common_dispatch(method, params):
    if method in ['get_running_requests']:
        passwd = params[0]
        params = params[1:]
        service.security.check_super(passwd)
        return globals()[method](*params)
    return native_common_dispatch(method, params)


common.dispatch = new_common_dispatch
common.get_running_requests = get_running_requests
