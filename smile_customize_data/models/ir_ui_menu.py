# -*- coding: utf-8 -*-
# (C) 2021 Smile (<http://www.smile.fr>)
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl).


from odoo import fields, models


class IrUiMenu(models.Model):
    _inherit = "ir.ui.menu"

    is_customized_menu = fields.Boolean(string='Customized menu', readonly=True)
