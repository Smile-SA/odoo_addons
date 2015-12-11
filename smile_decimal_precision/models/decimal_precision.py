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

from openerp import api, fields, models, registry, tools


class DecimalPrecision(models.Model):
    _inherit = 'decimal.precision'

    display_digits = fields.Integer('Display Digits', required=True, default=2)

    @tools.ormcache(skiparg=3)
    def display_precision_get(self, cr, uid, application):
        cr.execute('select display_digits from decimal_precision where name=%s', (application,))
        res = cr.fetchone()
        return res[0] if res else 2

    @api.model
    @api.returns('self', lambda value: value.id)
    def create(self, vals):
        record = super(DecimalPrecision, self).create(vals)
        self.display_precision_get.clear_cache(self)
        return record

    @api.multi
    def write(self, vals):
        result = super(DecimalPrecision, self).write(vals)
        self.display_precision_get.clear_cache(self)
        return result

    @api.multi
    def unlink(self):
        result = super(DecimalPrecision, self).unlink()
        self.display_precision_get.clear_cache(self)
        return result

    @staticmethod
    def get_display_precision(cr, uid, application):
        res = 2
        dp_obj = registry(cr.dbname)['decimal.precision']
        if hasattr(dp_obj, 'display_precision_get'):
            res = dp_obj.display_precision_get(cr, uid, application)
        return 16, res
