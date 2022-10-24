# -*- coding: utf-8 -*-
# (C) 2019 Smile (<http://www.smile.eu>)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

import logging

_logger = logging.getLogger(__name__)


def create_unique_index(cr, table, column, where_clause=None):
    if type(column) == list:
        column = ','.join(column)
    column_name = column.replace(' ', '').replace(',', '_')
    index_name = 'uniq_%(table)s_%(column_name)s' % locals()
    cr.execute("SELECT relname FROM pg_class WHERE relname=%s", (index_name,))
    if not cr.rowcount:
        _logger.debug('Creating unique index %s' % index_name)
        query = "CREATE UNIQUE INDEX %(index_name)s ON %(table)s (%(column)s)"
        query += " WHERE %s" % (where_clause or "%(column)s IS NOT NULL")
        query = query % locals()
        cr.execute(query)
