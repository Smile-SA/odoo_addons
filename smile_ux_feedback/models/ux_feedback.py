from odoo import models, fields


class UxFeedback(models.Model):
    _name = "ux.feedback"
    _description = "User Experience Feedback"
    _rec_name = "reference"

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
    timestamp = fields.Datetime(string="Timestamp",
                                default=fields.Datetime.now)
    url = fields.Char(string="URL")
    reference = fields.Char(string="Reference")
