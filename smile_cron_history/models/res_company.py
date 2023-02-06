# (C) 2023 Smile (<https://www.smile.eu>)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields, models


class ResCompany(models.Model):
    _inherit = 'res.company'

    alert_failure_email = fields.Char(
        'Alert Failure email',
        help='An alert will be sent to this email when a cron fails')
