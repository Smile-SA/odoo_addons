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

from odoo import api, fields, models, tools


class DecimalPrecision(models.Model):
    _inherit = 'decimal.precision'

    display_digits = fields.Integer('Display Digits', required=True, default=2)

    @api.model
    @tools.ormcache('application')
    def display_precision_get(self, application):
        self.env.cr.execute('select display_digits from decimal_precision where name=%s', (application,))
        res = self.env.cr.fetchone()
        return res[0] if res else 2

    @staticmethod
    def get_display_precision(env, application):
        res = 2
        dp = env['decimal.precision']
        if hasattr(dp, 'display_precision_get'):
            res = dp.display_precision_get(application)
        return 16, res
