# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2014 Smile (<http://www.smile.fr>).
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

from openerp import models

magic_fields = ['create_uid', 'create_date', 'write_uid', 'write_date']


def get_fields_to_export(self):
    fields_to_export = ['id']
    for column, field in self._fields.iteritems():
        if column in magic_fields:
            continue
        if field.type == 'one2many' \
                or not field.store:
            continue
        if field.type in ('many2many', 'many2one'):
            column += ':id'
        fields_to_export.append(column)
    return fields_to_export

models.Model.get_fields_to_export = get_fields_to_export
