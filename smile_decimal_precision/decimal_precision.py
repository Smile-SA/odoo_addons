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

from openerp import pooler, tools
from openerp.osv import orm, fields


class DecimalPrecision(orm.Model):
    _inherit = 'decimal.precision'

    _columns = {
        'display_digits': fields.integer('Display Digits', required=True),
    }

    _defaults = {
        'display_digits': 2,
    }

    @tools.ormcache(skiparg=3)
    def display_precision_get(self, cr, uid, application):
        cr.execute('select display_digits from decimal_precision where name=%s', (application,))
        res = cr.fetchone()
        return res[0] if res else 2

    def create(self, cr, uid, vals, context=None):
        res = super(DecimalPrecision, self).create(cr, uid, vals, context)
        self.display_precision_get.clear_cache(self)
        return res

    def write(self, cr, uid, ids, vals, context=None):
        res = super(DecimalPrecision, self).write(cr, uid, ids, vals, context)
        self.display_precision_get.clear_cache(self)
        return res

    def unlink(self, cr, uid, ids, context=None):
        res = super(DecimalPrecision, self).unlink(cr, uid, ids, context=context)
        self.display_precision_get.clear_cache(self)
        return res

    @staticmethod
    def get_display_precision(cr, uid, application):
        res = 2
        dp_obj = pooler.get_pool(cr.dbname).get('decimal.precision')
        if hasattr(dp_obj, 'display_precision_get'):
            res = dp_obj.display_precision_get(cr, uid, application)
        return (16, res)
