# -*- coding: utf-8 -*-
# (C) 2019 Smile (<http://www.smile.fr>)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields, models


class IrAttachment(models.Model):
    _inherit = 'ir.attachment'

    res_model = fields.Char(index=True)
    res_field = fields.Char(index=True)
    res_id = fields.Many2oneReference(index=True)
