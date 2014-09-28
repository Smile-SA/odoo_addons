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

from openerp import registry
from openerp.workflow.workitem import WorkflowItem

native_execute = WorkflowItem._execute


def new_execute(self, activity, stack):

    cr, uid, ids = self.session.cr, self.session.uid, [self.record.id]

    # Retrieve the action rules to possibly execute
    rule_obj = registry(self.session.cr.dbname)['base.action.rule']
    rules = rule_obj._get_action_rules_on_wkf(cr, uid, activity['id'])

    # Check preconditions
    pre_ids = {}
    for rule in rules:
        if rule.kind not in ('on_create', 'on_create_or_write'):
            pre_ids[rule] = rule_obj._filter(cr, uid, rule, rule.filter_pre_id, ids)

    # Call original method
    result = native_execute(self, activity, stack)

    # Check postconditions, and execute actions on the records that satisfy them
    for rule in rules:
        if rule.kind != 'on_unlink':
            post_ids = rule_obj._filter(cr, uid, rule, rule.filter_id, pre_ids[rule])
        else:
            post_ids = pre_ids[rule]
        if post_ids:
            rule_obj._process(cr, uid, rule, post_ids)

    return result

WorkflowItem._execute = new_execute
