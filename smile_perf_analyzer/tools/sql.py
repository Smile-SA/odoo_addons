# -*- coding: utf-8 -*-

from odoo.modules import registry
from odoo.service.db import _create_empty_database, DatabaseExists
from odoo.sql_db import db_connect
from odoo.tools import sql


def perf_cursor(dbname):
    perf_dbname = dbname + '_perf'
    try:
        _create_empty_database(perf_dbname)
    except DatabaseExists:
        pass
    return db_connect(perf_dbname).cursor()


native_existing_tables = sql.existing_tables


def existing_tables(cr, tablenames):
    res = []
    perf_log_tablename = 'ir_logging_perf_log'
    if perf_log_tablename in tablenames:
        tablenames = set(tablenames).difference({perf_log_tablename})
        res += native_existing_tables(
            perf_cursor(cr.dbname), {perf_log_tablename})
    if tablenames:
        res += native_existing_tables(cr, tablenames)
    return res


sql.existing_tables = existing_tables
registry.existing_tables = existing_tables
