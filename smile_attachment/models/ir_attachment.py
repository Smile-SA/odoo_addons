# -*- coding: utf-8 -*-
# (C) 2010 Smile (<http://www.smile.fr>)
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl).

from odoo import fields, models


class IrAttachment(models.Model):
    _inherit = 'ir.attachment'

    res_model = fields.Char(index=True)
    res_id = fields.Integer(index=True)
