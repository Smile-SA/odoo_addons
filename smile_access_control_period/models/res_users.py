# -*- coding: utf-8 -*-
# (C) 2020 Smile (<http://www.smile.fr>)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import api, fields, models, tools


class ResUsers(models.Model):
    _inherit = 'res.users'

    date_start = fields.Date('Read-only Start date')
    date_stop = fields.Date('Read-only End date')

    @api.model
    def _get_default_field_ids(self):
        return self.env['ir.model.fields'].search([
            ('model', 'in', ('res.users', 'res.partner')),
            ('name', 'in', ('action_id', 'menu_id', 'groups_id',
                            'date_start', 'date_stop')),
        ]).ids

    @api.model
    @tools.ormcache('self._uid')
    def get_readonly_dates(self):
        return self.env.user.date_start, self.env.user.date_stop

    @api.model
    def create(self, vals):
        user = super(ResUsers, self).create(vals)
        self.clear_caches()
        return user

    def write(self, vals):
        res = super(ResUsers, self).write(vals)
        self.clear_caches()
        return res
