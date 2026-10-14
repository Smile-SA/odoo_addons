from odoo import models, fields


class UxConformity(models.Model):
    _name = "ux.conformity"
    _description = "Conformity"

    name = fields.Char(string="Name",
                       required=True, translate=True)
