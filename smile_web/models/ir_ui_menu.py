# -*- coding: utf-8 -*-
# (C) 2018 Smile (<http://www.smile.fr>)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import api, models, tools


class IrUiMenu(models.Model):
    _inherit = 'ir.ui.menu'

    @api.model
    @tools.ormcache('frozenset(self.env.user.groups_id.ids)', 'debug')
    def _visible_menu_ids(self, debug=False):
        """ Hide hidden menus in navbar search provided by module
        web_responsive.
        Add a special case for module base_technical_features, forcing
        the display of technical menus hidden by default if user hasn't
        enable debug mode.
        """
        if not debug:
            debug = self.env.user.has_group(
                'base_technical_features.group_technical_features')
        visible_menu_ids = super(IrUiMenu, self)._visible_menu_ids(debug)
        groups = self.env.user.groups_id
        if not debug:
            groups = groups - self.env.ref('base.group_no_one')
        for menu in self.browse(visible_menu_ids):
            parent = menu.parent_id
            while parent:
                if parent.groups_id and not (parent.groups_id & groups):
                    visible_menu_ids.remove(menu.id)
                    break
                parent = parent.parent_id
        return visible_menu_ids
