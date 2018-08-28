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


class AccountPeriodClose(orm.TransientModel):
    _inherit = "account.period.close"

    def data_save(self, cr, uid, ids, context=None):
        assert len(ids) == 1, 'ids must be a list with only one item!'
        if self.browse(cr, uid, ids[0], context).sure:
            context = context or {}
            self.pool.get('account.period').post_depreciation_line(cr, uid, context['active_ids'], context=context)
        return super(AccountPeriodClose, self).data_save(cr, uid, ids, context)
