# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2015 Smile (<http://www.smile.fr>). All Rights Reserved
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


class unquote(str):

    def __getitem__(self, key):
        return unquote('%s[%s]' % (self, key))

    def __getattribute__(self, attr):
        return unquote('%s.%s' % (self, attr))

    def __call__(self, *args, **kwargs):
        format_args = lambda k: isinstance(k, basestring) and '"%s"' % k or k
        format_kwargs = lambda (k, v): '%s=%s' % (k, isinstance(v, basestring) and '"%s"' % v or v)
        params = [', '.join(map(format_args, args)),
                  ', '.join(map(format_kwargs, kwargs.iteritems()))]
        return unquote('%s(%s)' % (self, ', '.join(params)))

    def __repr__(self):
        return self
