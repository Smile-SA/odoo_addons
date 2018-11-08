# -*- coding: utf-8 -*-
# (C) 2018 Smile (<http://www.smile.fr>)
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl).

import sys

from odoo import api

if sys.version_info > (3,):
    long = int


def audit_decorator(method):

    def get_audit_rule(self, method):
        AuditRule = self.env['audit.rule']
        group_ids = self.env.user.groups_id.ids
        rule_id = AuditRule._check_audit_rule(group_ids).get(
            self._name, {}).get(method)
        return AuditRule.browse(rule_id) if rule_id else None

    @api.model
    def audit_create(self, vals):
        result = audit_create.origin(self, vals)
        record = self.browse(result) if isinstance(result, (int, long)) \
            else result
        rule = get_audit_rule(self, 'create')
        if rule:
            new_values = record.read(load='_classic_write')
            rule.log('create', new_values=new_values)
        return result

    @api.multi
    def audit_write(self, vals):
        rule = get_audit_rule(self, 'write')
        if rule:
            old_values = self.read(load='_classic_write')
        result = audit_write.origin(self, vals)
        if rule:
            new_values = self.read(load='_classic_write')
            rule.log('write', old_values, new_values)
        return result

    @api.multi
    def audit_unlink(self):
        rule = get_audit_rule(self, 'unlink')
        if rule:
            old_values = self.read(load='_classic_write')
            rule.log('unlink', old_values)
        return audit_unlink.origin(self)

    if 'create' in method:
        return audit_create
    if 'write' in method:
        return audit_write
    if 'unlink' in method:
        return audit_unlink
