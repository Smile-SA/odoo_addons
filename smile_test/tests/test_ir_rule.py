# -*- coding: utf-8 -*-

from odoo.tests.common import TransactionCase


class TestIrRule(TransactionCase):
    def _get_ir_rules_to_ignore(self):
        # Native ir.rule not formated with Smile guidelines
        xml_ids = []
        return [
            self.env.ref(xml_id).id
            for xml_id in xml_ids
            if self.env.ref(xml_id, False)
        ]

    def test_check_ir_rules(self):
        """I check all ir.rule."""
        errors = []
        # Search all rules having a domain
        rules_to_ignore = self._get_ir_rules_to_ignore()
        domain = [
            ("domain_force", "!=", False),
            ("id", "not in", rules_to_ignore),
        ]
        fields_to_read = ["name", "domain_force"]
        rule_domains = self.env["ir.rule"].search_read(domain, fields_to_read)
        # Evaluated domain of found rules
        eval_context = self.env["ir.rule"]._eval_context()
        for rule_info in rule_domains:
            domain_force = rule_info["domain_force"] or "[]"
            rule_info["domain_force"] = eval(
                compile(domain_force.strip(), "", mode="eval"), eval_context
            )
        # Ensure that all found rules are well formated
        for rule_info in rule_domains:
            expr_nb = 0
            operator_nb = 0
            for part in rule_info["domain_force"]:
                if part == "!":
                    continue
                elif part in ("&", "|"):
                    operator_nb += 1
                else:
                    expr_nb += 1
            if rule_info and operator_nb > 0 and (expr_nb - operator_nb) != 1:
                # If there is at least an operator in domain, ensure
                # that all operators are explicitely defined
                errors.append(
                    (
                        rule_info["name"],
                        rule_info["domain_force"],
                        expr_nb,
                        operator_nb,
                    )
                )
        err_details = "\n".join(
            "%s: %s - %s/%s" % rule_infos for rule_infos in errors
        )
        error_msg = "Check theses ir.rule:\n%s" % err_details
        self.assertEqual(len(errors), 0, error_msg)
