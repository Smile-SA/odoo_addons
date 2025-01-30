# -*- coding: utf-8 -*-
# (C) 2022 Smile (<https://www.smile.eu>)
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl).

from odoo import api, models


class IrUiMenu(models.Model):
    _inherit = 'ir.ui.menu'

    @api.model
    def search_count(self, domain, limit=None):
        """ Hide Administrators menu to users that are not ERP managers
        """
        if not self.user_has_groups('base.group_system'):
            menu_id = self.env['ir.model.data']._xmlid_to_res_id('smile_access_control.menu_action_administrators')
            args = [('id', '!=', menu_id)] + (args or [])
        return super(IrUiMenu, self).search_count(domain, limit)
