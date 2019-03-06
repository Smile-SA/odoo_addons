# -*- coding: utf-8 -*-
# (C) 2019 Smile (<http://www.smile.fr>)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields, models


class ResGroups(models.Model):
    _inherit = 'res.groups'

    website_menu_ids = fields.Many2many(
        'website.menu', 'website_menu_res_group_rel',
        'group_id', 'menu_id', 'Website menus')
