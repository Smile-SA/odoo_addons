# -*- coding: utf-8 -*-
# (C) 2018 Smile (<http://www.smile.fr>)
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl).

import datetime

from odoo import api, fields, models
from odoo.tools.safe_eval import safe_eval


class Base(models.AbstractModel):
    _inherit = "base"

    @api.multi
    def _read_from_database(self, field_names, inherited_field_names=[]):
        super(Base, self)._read_from_database(
            field_names, inherited_field_names)
        # Store history revision in cache
        if self._context.get('history_revision'):
            group_ids = self.env.user.groups_id.ids
            audit_rules = self.env['audit.rule']._check_audit_rule(
                group_ids).get(self._name, {})
            if audit_rules:
                history_date = fields.Datetime.from_string(
                    self._context.get('history_revision'))
                date_operator = audit_rules.get('create') and '>' or '>='
                domain = [
                    ('model', '=', self._name),
                    ('res_id', 'in', self.ids),
                    ('create_date', date_operator, history_date),
                ]
                logs = self.env['audit.log'].sudo().search(
                    domain, order='create_date desc')
                for record in self:
                    vals = {}
                    for log in logs:
                        if log.res_id == record.id:
                            data = safe_eval(log.data or '{}',
                                             {'datetime': datetime})
                            vals.update(data.get('old', {}))
                    if 'message_ids' in self._fields:
                        vals['message_ids'] = record.message_ids.filtered(
                            lambda msg: msg.date <= history_date)
                    record._cache.update(record._convert_to_cache(
                        vals, validate=False))

    @api.model
    def fields_get(self, allfields=None, attributes=None):
        res = super(Base, self).fields_get(allfields, attributes)
        if self.env.context.get('history_revision'):
            for field in res:
                res[field]['readonly'] = True
        return res

    @api.model
    def _get_audit_rule(self, method):
        AuditRule = self.env['audit.rule']
        group_ids = self.env.user.groups_id.ids
        rule_id = AuditRule._check_audit_rule(group_ids).get(
            self._name, {}).get(method)
        return AuditRule.browse(rule_id) if rule_id else None

    @api.model_create_multi
    def create(self, vals_list):
        if not self._get_audit_rule('create') or not (
                self.env.recompute and self._context.get('recompute', True)):
            return super(Base, self).create(vals_list)
        audit_ctx = dict(self._context)
        audit_ctx.setdefault('do_not_recompute_for', [])
        audit_ctx['do_not_recompute_for'].append(self._name)
        records = super(Base, self.with_context(audit_ctx)).create(vals_list)
        self.with_context({
            'audit_rec_model': self._name,
            'audit_rec_ids': records.ids,
        }).recompute()
        return records

    @api.model
    def recompute(self):
        if self._name not in self._context.get('do_not_recompute_for', []):
            super(Base, self).recompute()

    def concat(self, *args):
        records = super(Base, self).concat(*args)
        if args and args[0]._context.get('audit_rec_model') == self._name:
            records = records.with_context({
                'audit_rec_model': self._name,
                'audit_rec_ids': records.ids,
            })
        return records

    @api.model
    def _create(self, data_list):
        records = super(Base, self)._create(data_list)
        if self._get_audit_rule('create'):
            for data in data_list:
                data['record'] = data['record'].with_context({
                    'audit_rec_model': self._name,
                    'audit_rec_ids': data['record'].ids,
                })
        return records

    @api.multi
    def write(self, vals):
        if not self._get_audit_rule('write'):
            return super(Base, self).write(vals)
        return super(Base, self.with_context({
            'audit_rec_model': self._name,
            'audit_rec_ids': self.ids,
        })).write(vals)
