from odoo import models, fields


class UxSatisfaction(models.Model):
    _name = "ux.satisfaction"
    _description = "Satisfaction"

    name = fields.Char(string="Name",
                       required=True, translate=True)
