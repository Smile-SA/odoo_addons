# -*- encoding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2011 Smile (<http://www.smile.fr>). All Rights Reserved
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

from odoo import api, fields, models, tools
from odoo.http import request


class WebsiteMenu(models.Model):
    _inherit = 'website.menu'

    groups_id = fields.Many2many('res.groups', 'website_menu_res_group_rel',
                                 'menu_id', 'group_id', 'Groups')

    @api.model
    @tools.ormcache('frozenset(self.env.user.groups_id.ids)', 'debug')
    def _get_visible_menu_ids(self, debug=False):
        """ Return the ids of the menu items visible to the user. """
        # retrieve all menus, and determine which ones are visible
        context = {'website.menu.full_list': True}
        menus = self.with_context(**context).search([])

        # discard all menus with groups the user does not have
        groups = self.env.user.groups_id
        if not debug:
            groups = groups - self.env.ref('base.group_no_one')
        menus = menus.filtered(lambda menu: not menu.groups_id or menu.groups_id & groups)

        # make menu visible unless its ancestor is not visible
        visible = self.browse(menus.ids)
        for menu in menus:
            while menu:
                menu = menu.parent_id
                if menu not in visible:
                    break
            else:
                visible |= menu
        return set(visible.ids)

    @api.multi
    @api.returns('self')
    def filter_visible_menus(self):
        visible_ids = self._get_visible_menu_ids(request.debug if request else False)
        return self.filtered(lambda menu: menu.id in visible_ids)

    @api.model
    def search(self, args, offset=0, limit=None, order=None, count=False):
        menus = super(WebsiteMenu, self).search(args, offset=0, limit=None, order=order, count=False)
        if menus:
            if not self._context.get('website.menu.full_list'):
                menus = menus.filter_visible_menus()
            if offset:
                menus = menus[long(offset):]
            if limit:
                menus = menus[:long(limit)]
        return len(menus) if count else menus

    @api.model
    def create(self, values):
        self.clear_caches()
        return super(WebsiteMenu, self).create(values)

    @api.multi
    def write(self, values):
        self.clear_caches()
        return super(WebsiteMenu, self).write(values)

    @api.multi
    def unlink(self):
        # Detach children and promote them to top-level, because it would be unwise to
        # cascade-delete submenus blindly. We also can't use ondelete=set null because
        # that is not supported when _parent_store is used (would silently corrupt it).
        # TODO: ideally we should move them under a generic "Orphans" menu somewhere?
        context = {'website.menu.full_list': True}
        direct_children = self.with_context(**context).search([('parent_id', 'in', self.ids)])
        direct_children.write({'parent_id': False})

        self.clear_caches()
        return super(WebsiteMenu, self).unlink()
