from odoo import models, fields, api
from odoo.exceptions import ValidationError
import ast


class DynamicActionRule(models.Model):
    _name = "dynamic.action.rule"
    _description = "Dynamic Action Visibility Rule"
    _order = "sequence, id"

    name = fields.Char(required=True)
    active = fields.Boolean(default=True)
    sequence = fields.Integer(default=10)

    model_id = fields.Many2one(
        "ir.model",
        string="Model",
        required=True,
        ondelete="cascade",
    )
    action_id = fields.Many2one(
        "ir.actions.actions",
        domain="[('binding_model_id', '=', model_id)]",
        required=True,
    )

    condition = fields.Text(
        required=True,
        help="""
                Python expression evaluated on record.
                Available variable:
                 - record
                Example:
                record.state != 'validated'
                record.service_type_id.id == 3
                """,
    )

    @api.constrains("condition")
    def _check_condition(self):
        for rule in self:
            try:
                ast.parse(rule.condition)
            except Exception as e:
                raise ValidationError(f"Invalid condition:\n{e}")
