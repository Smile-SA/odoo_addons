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

from openerp import fields, models, pooler, tools


class DecimalPrecision(models.Model):
    _inherit = 'decimal.precision'

    display_digits = fields.Integer('Display Digits', required=True, default=2)

    @tools.ormcache(skiparg=3)
    def display_precision_get(self, cr, uid, application):
        cr.execute('select display_digits from decimal_precision where name=%s', (application,))
        res = cr.fetchone()
        return res[0] if res else 2

    def create(self, cr, uid, vals, context=None):
        record = super(DecimalPrecision, self).create(cr, uid, vals, context=None)
        self.display_precision_get.clear_cache(self)
        return record

    def write(self, cr, uid, ids, vals, context=None):
        result = super(DecimalPrecision, self).write(cr, uid, ids, vals, context=None)
        self.display_precision_get.clear_cache(self)
        return result

    def unlink(self, cr, uid, ids, context=None):
        result = super(DecimalPrecision, self).unlink(cr, uid, ids, context)
        self.display_precision_get.clear_cache(self)
        return result

    @staticmethod
    def get_display_precision(cr, uid, application):
        res = 2
        dp_obj = pooler.get_pool(cr.dbname).get('decimal.precision')
        if hasattr(dp_obj, 'display_precision_get'):
            res = dp_obj.display_precision_get(cr, uid, application)
        return (16, res)
