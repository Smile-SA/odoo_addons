# -*- encoding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2010 Smile (<http://www.smile.fr>). All Rights Reserved
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

from openerp import api, tools, models, fields


class IrUiMenu(models.Model):
    _inherit = 'ir.ui.menu'

    fa_icon = fields.Char('Font Awesome Icon', help='Given icon must appear on the left of menu label.')

    @api.multi
    def read(self, fields=None, load='_classic_read'):
        fields = fields or []
        fields += self._context.get('new_menu_fields_to_read', [])
        return super(IrUiMenu, self).read(fields, load)

    @api.model
    @tools.ormcache_context(keys=('lang',))
    def load_menus_root(self):
        self = self.with_context(new_menu_fields_to_read=['fa_icon'])
        res = super(IrUiMenu, self).load_menus_root()
        self = self.with_context(new_menu_fields_to_read=[])
        return res

    @api.model
    @tools.ormcache_context('debug', keys=('lang',))
    def load_menus(self, debug):
        self = self.with_context(new_menu_fields_to_read=['fa_icon'])
        res = super(IrUiMenu, self).load_menus(debug)
        self = self.with_context(new_menu_fields_to_read=[])
        return res
