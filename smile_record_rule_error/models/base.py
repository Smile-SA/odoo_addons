# -*- coding: utf-8 -*-
# (C) 2018 Smile (<http://www.smile.fr>)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import api, models, tools
from odoo.exceptions import AccessError, UserError
from odoo.osv import expression


class Base(models.AbstractModel):
    _inherit = 'base'

    @api.multi
    def check_access_rule(self, operation):
        try:
            super(Base, self).check_access_rule(operation)
        except AccessError:
            Rule = self.env['ir.rule']
            rule_ids = Rule._get_rules_to_apply(self._name, operation)
            rules = Rule.sudo().with_context(
                lang=self.env.user.lang).browse(rule_ids)
            global_rules = rules.filtered(lambda rule: not rule.groups)
            for rule in global_rules:
                if not rule.domain_force:
                    continue
                domain = tools.safe_eval(
                    rule.domain_force, rule._eval_context())
                domain = expression.normalize_domain(
                    [('id', 'in', self.ids)] + domain)
                records_count = self.search_count(domain)
                if records_count < len(self):
                    if rule.error_message:
                        raise UserError(rule.error_message)
                    break
            else:
                group_rules = rules - global_rules
                error_messages = group_rules.mapped('error_message')
                if all(error_messages):
                    raise UserError("\n\n".join(error_messages))
            raise
