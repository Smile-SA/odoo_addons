import logging
from odoo import models, api

_logger = logging.getLogger(__name__)


class IrActions(models.Model):
    _inherit = "ir.actions.actions"

    @api.model
    def get_invisible_action_ids(self, model, res_ids, action_ids):
        """
        Return action IDs that must be hidden according to dynamic.action.rule.

        - If res_ids is empty: hide all actions having rules for this model
        - If multiple records are selected:
            → hide the action if ANY record satisfies the rule
        """
        self = self.sudo()

        if not action_ids:
            return []

        rules = self.env["dynamic.action.rule"].search(
            [
                ("model_id.model", "=", model),
                ("action_id", "in", action_ids),
            ]
        )

        if not rules:
            return []

        # No active records → hide all ruled actions
        if not res_ids:
            return list(rules.mapped("action_id").ids)

        records = self.env[model].browse(res_ids).exists()
        if not records:
            return []

        invisible_ids = set()
        safe_globals = {"__builtins__": {}}

        for rule in rules:
            for record in records:
                try:
                    if eval(rule.condition, safe_globals, {"record": record}):
                        invisible_ids.add(rule.action_id.id)
                        break  # ONE record is enough → hide
                except Exception as e:
                    _logger.error(
                        "Dynamic Action Visibility: failed to evaluate condition '%s' "
                        "for action '%s' (model=%s, record_id=%s). Error: %s",
                        rule.condition,
                        rule.action_id.name,
                        record._name,
                        record.id,
                        e,
                    )

        return list(invisible_ids)
