from odoo import models, fields


class UxPerformance(models.Model):
    _name = "ux.performance"
    _description = "Performance"

    name = fields.Char(string="Name",
                       required=True, translate=True)
