# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

import logging
import psycopg2
from odoo.tools import sql

_schema = logging.getLogger('odoo.schema')

_TABLE_KIND = {
    'BASE TABLE': 'r',
    'VIEW': 'v',
    'FOREIGN TABLE': 'f',
    'LOCAL TEMPORARY': 't',
}

_CONFDELTYPES = {
    'RESTRICT': 'r',
    'NO ACTION': 'a',
    'CASCADE': 'c',
    'SET NULL': 'n',
    'SET DEFAULT': 'd',
}


def existing_tables(cr, tablenames):
    """ Return the names of existing tables among ``tablenames``. """
    query = """
        SELECT c.relname
          FROM pg_class c
          JOIN pg_namespace n ON (n.oid = c.relnamespace)
         WHERE c.relname IN %s
           AND c.relkind IN ('r', 'v', 'm')
           AND n.nspname = 'public'
    """
    cr.execute(query, [tuple(tablenames)])
    return [row[0] for row in cr.fetchall()]


def table_exists(cr, tablename):
    """ Return whether the given table exists. """
    return len(existing_tables(cr, {tablename})) == 1


def table_columns(cr, tablename):
    """ Return a dict mapping column names to their configuration. The latter is
        a dict with the data from the table ``information_schema.columns``.
    """
    # Do not select the field `character_octet_length` from `information_schema.columns`
    # because specific access right restriction in the context of shared hosting (Heroku, OVH, ...)
    # might prevent a postgres user to read this field.
    query = '''SELECT column_name, udt_name, character_maximum_length, is_nullable
               FROM information_schema.columns WHERE table_name=%s'''
    cr.execute(query, (tablename,))
    return {row['column_name']: row for row in cr.dictfetchall()}


def create_column(cr, tablename, columnname, columntype, comment=None):
    """ Create a column with the given type. """
    cr.execute('ALTER TABLE "{}" ADD COLUMN "{}" {}'.format(tablename, columnname, columntype))
    if comment:
        cr.execute('COMMENT ON COLUMN "{}"."{}" IS %s'.format(tablename, columnname), (comment,))
    _schema.debug("Table %r: added column %r of type %s", tablename, columnname, columntype)


def rename_column(cr, tablename, columnname1, columnname2):
    """ Rename the given column. """
    cr.execute('ALTER TABLE "{}" RENAME COLUMN "{}" TO "{}"'.format(tablename, columnname1, columnname2))
    _schema.debug("Table %r: renamed column %r to %r", tablename, columnname1, columnname2)


def convert_column(cr, tablename, columnname, columntype):
    """ Convert the column to the given type. """
    try:
        with cr.savepoint():
            cr.execute('ALTER TABLE "{}" ALTER COLUMN "{}" TYPE {}'.format(tablename, columnname, columntype),
                       log_exceptions=False)
    except psycopg2.NotSupportedError:
        # can't do inplace change -> use a casted temp column
        query = '''
            ALTER TABLE "{0}" RENAME COLUMN "{1}" TO __temp_type_cast;
            ALTER TABLE "{0}" ADD COLUMN "{1}" {2};
            UPDATE "{0}" SET "{1}"= __temp_type_cast::{2};
            ALTER TABLE "{0}" DROP COLUMN  __temp_type_cast CASCADE;
        '''
        cr.execute(query.format(tablename, columnname, columntype))
    _schema.debug("Table %r: column %r changed to type %s", tablename, columnname, columntype)


def column_exists(cr, tablename, columnname):
    """ Return whether the given column exists. """
    query = """ SELECT 1 FROM information_schema.columns
                WHERE table_name=%s AND column_name=%s """
    cr.execute(query, (tablename, columnname))
    return cr.rowcount


def drop_not_null(cr, tablename, columnname):
    """ Drop the NOT NULL constraint on the given column. """
    cr.execute('ALTER TABLE "{}" ALTER COLUMN "{}" DROP NOT NULL'.format(tablename, columnname))
    _schema.debug("Table %r: column %r: dropped constraint NOT NULL", tablename, columnname)


sql.create_column = create_column
sql.rename_column = rename_column
sql.convert_column = convert_column
sql.column_exists = column_exists
sql.drop_not_null = drop_not_null
