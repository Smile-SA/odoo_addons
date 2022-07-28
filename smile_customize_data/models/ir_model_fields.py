# -*- coding: utf-8 -*-
# (C) 2020 Smile (<http://www.smile.fr>)
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl).


from odoo import fields, models


class IrModelFields(models.Model):
    _inherit = 'ir.model.fields'

    is_customized_field = fields.Boolean(
        string='Customized field', readonly=True)
