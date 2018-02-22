# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo.fields import Field

native_search_company_dependent = Field._search_company_dependent


def _search_company_dependent(self, records, operator, value):
    Property = records.env['ir.property']
    if 'company_id' in records._fields:
        Property = Property.with_context(
            force_company_ids=records.mapped('company_id').ids)
    return Property.search_multi(self.name, self.model_name, operator, value)


Field._search_company_dependent = _search_company_dependent
