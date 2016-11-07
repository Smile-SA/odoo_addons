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

from odoo import api, fields, models


class ResUsers(models.Model):
    _inherit = 'res.users'

    login_as_user_id = fields.Many2one('res.users', 'Login as')

    @api.multi
    def login_as(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_url',
            'url': '/',
            'target': 'new',
        }

    @api.multi
    def logout_as(self):
        return self.write({'login_as_user_id': False})
