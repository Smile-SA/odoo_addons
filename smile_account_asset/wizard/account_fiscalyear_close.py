# -*- encoding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2012 Smile (<http://www.smile.fr>). All Rights Reserved
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

from osv import orm


class AccountFiscalyearClose(orm.TransientModel):
    _inherit = "account.fiscalyear.close"

    def data_save(self, cr, uid, ids, context=None):
        assert len(ids) == 1, 'ids must be a list with only one item!'
        self.browse(cr, uid, ids[0], context).fy_id.create_inventory_entry()
        return super(AccountFiscalyearClose, self).data_save(cr, uid, ids, context)


class AccountFiscalyearCloseState(orm.TransientModel):
    _inherit = "account.fiscalyear.close.state"

    def data_save(self, cr, uid, ids, context=None):
        assert len(ids) == 1, 'ids must be a list with only one item!'
        self.browse(cr, uid, ids[0], context).fy_id.create_inventory_entry()
        return super(AccountFiscalyearCloseState, self).data_save(cr, uid, ids, context)
