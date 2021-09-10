# -*- coding: utf-8 -*-
# (C) 2019 Smile (<https://www.smile.eu>)
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl).

from odoo import fields, models


class IrActionsServer(models.Model):
    _inherit = 'ir.actions.server'

    groups_id = fields.Many2many('res.groups', 'server_groups_rel',
                                 'server_id', 'group_id', string='Groups')
