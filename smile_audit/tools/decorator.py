# -*- encoding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2010 Smile (<http://www.smile.fr>). All Rights Reserved
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

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
