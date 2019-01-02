# -*- coding: utf-8 -*-
# (C) 2011 Smile (<http://www.smile.fr>)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import models

magic_fields = ['create_uid', 'create_date', 'write_uid', 'write_date']


def get_fields_to_export(self):
    fields_to_export = []
    for column, field in self._fields.items():
        if column in magic_fields:
            continue
        if field.type == 'one2many' \
                or not field.store:
            continue
        if field.type in ('many2many', 'many2one'):
            column += ':id'
        fields_to_export.append(column)
    if 'id' not in fields_to_export:
        fields_to_export.append('id')
    return fields_to_export


models.Model.get_fields_to_export = get_fields_to_export
