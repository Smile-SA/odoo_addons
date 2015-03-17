# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2015 Smile (<http://www.smile.fr>).
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

{
    "name": "Followers",
    "version": "1.0",
    "author": "Smile",
    "website": 'http://www.smile.fr',
    "category": "Tools",
    "description": """
Manage models following
------------------------------------

* Disable auto-subscribe for users
** activation from user preferences

TODO: add code comments
TODO: describe usage


Code sample

from openerp.addons.smile_followers.tools import AddFollowers, add_followers


@AddFollowers()
class StockMove(models.Model):
    _name = 'stock.move'
    _inherit = ['stock.move', 'mail.thread']

    @add_followers()
    @api.model
    def create(self, vals):
        return super(StockMove, self).create(vals)

    @add_followers()
    @api.multi
    def write(self, vals):
        return super(StockMove, self).write(vals)

Suggestions & Feedback to: isabelle.richard@smile.fr
""",
    "depends": [
        'base',
        'mail',
    ],
    "data": [
        'views/res_partner_view.xml',
        'views/res_users_view.xml',
    ],
    "demo": [],
    "installable": True,
    "active": False,
}
