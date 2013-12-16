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

from openerp import tools
from openerp.osv import orm, fields


class ResUser(orm.Model):
    _inherit = 'res.users'

    _columns = {
        'date_start': fields.date('Read-only Start date'),
        'date_stop': fields.date('Read-only End date'),
    }

    def _get_default_field_ids(self, cr, uid, context=None):
        return self.pool.get('ir.model.fields').search(cr, uid, [
            ('model', '=', 'res.users'),
            ('name', 'in', ('action_id', 'menu_id', 'groups_id', 'view', 'date_start', 'date_stop')),
        ], context=context)

    _defaults = {
        'field_ids': _get_default_field_ids,
    }

    @tools.ormcache()
    def get_readonly_dates(self, cr, uid, user_id, context=None):
        user = self.read(cr, uid, uid, ['date_start', 'date_stop'], context)
        return user['date_start'], user['date_stop']

    def create(self, cr, uid, vals, context=None):
        res_id = super(ResUser, self).create(cr, uid, vals, context)
        self.get_readonly_dates.clear_cache(self)
        return res_id

    def write(self, cr, uid, ids, vals, context=None):
        res = super(ResUser, self).write(cr, uid, ids, vals, context)
        self.get_readonly_dates.clear_cache(self)
        return res
