# -*- coding: utf-8 -*-
# (C) 2018 Smile (<http://www.smile.fr>)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import api, fields, models, tools


class DecimalPrecision(models.Model):
    _inherit = 'decimal.precision'

    display_digits = fields.Integer(
        'Display Digits', required=True, default=2)

    @api.model
    @tools.ormcache('application')
    def display_precision_get(self, application):
        self.env.cr.execute(
            'select display_digits from decimal_precision where name=%s',
            (application,))
        res = self.env.cr.fetchone()
        return res[0] if res else 2

    @staticmethod
    def get_display_precision(env, application):
        res = 2
        dp = env['decimal.precision']
        if hasattr(dp, 'display_precision_get'):
            res = dp.display_precision_get(application)
        return 16, res
