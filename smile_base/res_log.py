# -*- encoding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2013 Smile (<http://www.smile.fr>). All Rights Reserved
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

from datetime import datetime, timedelta

from openerp.osv import orm


class ResLog(orm.Model):
    _inherit = 'res.log'

    def purge(self, cr, uid, days=60, context=None):
        limit_date = (datetime.today() - timedelta(days)).strftime('%Y-%m-%d')
        ids = self.search(cr, uid, [('read', '=', True), ('create_date', '<', limit_date)], context=context)
        return self.unlink(cr, uid, ids, context)
