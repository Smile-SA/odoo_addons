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

from openerp import models, SUPERUSER_ID


class IrUiMenu(models.Model):
    _inherit = 'ir.ui.menu'

    def _search(self, cr, uid, args, offset=0, limit=None, order=None, context=None, count=False, access_rights_uid=None):
        if uid != SUPERUSER_ID:
            xml_id = 'smile_access_control.menu_action_superadmin'
            menu_id = self.pool['ir.model.data'].xmlid_to_res_id(cr, uid, xml_id)
            args = [('id', '!=', menu_id)] + (args or [])
        return super(IrUiMenu, self)._search(cr, uid, args, offset, limit, order, context, count, access_rights_uid)
