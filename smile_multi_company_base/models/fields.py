# -*- coding: utf-8 -*-
# (C) 2018 Smile (<http://www.smile.eu>)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo.fields import Field

native_search_company_dependent = Field._search_company_dependent


def _search_company_dependent(self, records, operator, value):
    Property = records.env['ir.property']
    if 'company_id' in records._fields:
        Property = Property.with_context(
            force_company_ids=records.mapped('company_id').ids)
    return Property.search_multi(self.name, self.model_name, operator, value)


Field._search_company_dependent = _search_company_dependent
