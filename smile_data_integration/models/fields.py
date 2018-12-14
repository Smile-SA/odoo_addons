# -*- coding: utf-8 -*-

from odoo.tools import sql
from odoo.fields import Field


###########################################################################
#
# Update database schema
#


def update_db_column(self, model, column):
    """ Create/update the column corresponding to ``self``.

        :param model: an instance of the field's model
        :param column: the column's configuration (dict) if it exists, or ``None``
    """
    if not column:
        # the column does not exist, create it
        sql.create_column(model._cr, model._table, self.name, self.column_type[1], self.string)
        return
    if column['udt_name'] == self.column_type[0]:
        return
    if column['udt_name'] in self.column_cast_from:
        sql.convert_column(model._cr, model._table, self.name, self.column_type[1])
    else:
        newname = (self.name + '_moved{}').format
        i = 0
        while sql.column_exists(model._cr, model._table, newname(i)):
            i += 1
        if column['is_nullable'] == 'NO':
            sql.drop_not_null(model._cr, model._table, self.name)
        sql.rename_column(model._cr, model._table, self.name, newname(i))
        sql.create_column(model._cr, model._table, self.name, self.column_type[1], self.string)


Field.update_db_column = update_db_column
