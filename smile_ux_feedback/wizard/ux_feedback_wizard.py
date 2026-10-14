from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class UxFeedbackWizard(models.Model):
    _name = "ux.feedback.wizard"
    _description = "User Feedback Wizard"

    performance_id = fields.Many2one(
        "ux.performance", string="Performance")
    conformity_id = fields.Many2one("ux.conformity",
                                    string="Conformity")
    satisfaction_id = fields.Many2one(
        "ux.satisfaction", string="Satisfaction")
    feedback = fields.Text(string="Feedback")
    user_id = fields.Many2one(
        "res.users", string="User", default=lambda self: self.env.user
    )
    timestamp = fields.Datetime(
        string="Timestamp", default=fields.Datetime.now)
    url = fields.Char(string="URL")
    reference = fields.Char(string="Reference",
                            compute="_compute_reference", store=True)

    def action_submit_feedback(self):
        self.env["ux.feedback"].create(
            {
                "performance_id": self.performance_id.id,
                "conformity_id": self.conformity_id.id,
                "satisfaction_id": self.satisfaction_id.id,
                "feedback": self.feedback,
                "user_id": self.user_id.id,
                "timestamp": self.timestamp,
                "url": self.url,
                "reference": self.reference,
            }
        )

    @api.depends("timestamp", "url")
    def _compute_reference(self):
        for record in self:
            record.reference = self._compute_reference_value(record)

    def _compute_reference_value(self, record):
        timestamp = record.timestamp
        url = record.url
        if timestamp and url:
            date_str = timestamp.strftime("%Y%m%d")
            url_part = url.split("/odoo/")[1].split("/")[0].split("?")[0]
            return f"{date_str}_{url_part}"
        else:
            return "No Reference"

    @api.constrains("performance_id", "conformity_id", "satisfaction_id")
    def _check_required_fields(self):
        for record in self:
            if not (
                record.performance_id or (
                    record.conformity_id) or record.satisfaction_id):
                raise ValidationError(_("Performance, Conformity, "
                                        "and Satisfaction fields "
                                        "must be filled."))
