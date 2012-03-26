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

from osv import osv

class IrModelAccess(osv.osv):
    _inherit = 'ir.model.access'

    def get_perms(self, cr, uid, model, context=None):
        perms = {'create': True, 'write': True, 'unlink': True}
        if uid == 1:
            # User root have all accesses
            return perms
        cr.execute("""SELECT
MAX(CASE WHEN perm_create THEN 1 ELSE 0 END) as create,
MAX(CASE WHEN perm_write THEN 1 ELSE 0 END) as write,
MAX(CASE WHEN perm_unlink THEN 1 ELSE 0 END) as unlink
FROM ir_model_access a
JOIN ir_model m ON (m.id = a.model_id)
JOIN res_groups_users_rel gu ON (gu.gid = a.group_id)
WHERE m.model = %s AND gu.uid = %s""", (model, uid))
        perms = cr.dictfetchone()
        return perms
IrModelAccess()
