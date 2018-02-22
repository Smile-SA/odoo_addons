# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, models


class IrProperty(models.Model):
    _inherit = 'ir.property'

    @api.model
    def _get_record_ids_by_company_id(self, model, ids):
        record_ids_by_company_id = {}
        for record in self.env[model].browse(ids):
            record_ids_by_company_id.setdefault(
                record.company_id.id, []).append(record.id)
        return record_ids_by_company_id

    @api.model
    def get_multi(self, name, model, ids):
        if 'company_id' not in self.env[model]._fields or \
                name == 'company_id':
            return super(IrProperty, self).get_multi(name, model, ids)
        record_ids_by_company_id = self._get_record_ids_by_company_id(
            model, ids)
        result = {}
        for company_id, record_ids in record_ids_by_company_id.items():
            self = self.with_context(force_company=company_id)
            result.update(super(IrProperty, self).get_multi(
                name, model, record_ids))
        return result

    @api.model
    def set_multi(self, name, model, values, default_value=None):
        if 'company_id' not in self.env[model]._fields or \
                name == 'company_id':
            return super(IrProperty, self).set_multi(
                name, model, values, default_value)
        # TODO: check default_value if model,name is a relational field
        # and has a company_id field
        record_ids_by_company_id = self._get_record_ids_by_company_id(
            model, values.keys())
        for company_id, record_ids in record_ids_by_company_id.items():
            self = self.with_context(force_company=company_id)
            record_values = {record_id: values[record_id]
                             for record_id in record_ids}
            super(IrProperty, self).set_multi(
                name, model, record_values, default_value)

    @api.model
    def search_multi(self, name, model, operator, value):
        if not self._context.get('force_company'):
            force_companies = self.env.user.company_id._get_all_children()
            self = self.with_context(force_company_ids=force_companies.ids)
        return super(IrProperty, self).search_multi(
            name, model, operator, value)

    def _get_domain(self, prop_name, model):
        domain = super(IrProperty, self)._get_domain(prop_name, model)
        if self._context.get('force_company_ids'):
            for cond in domain:
                if isinstance(cond, (list, tuple)):
                    if cond[0] == 'company_id':
                        ids = self._context.get('force_company_ids')
                        cond = (cond[0], cond[1], ids + [False])
        return domain
