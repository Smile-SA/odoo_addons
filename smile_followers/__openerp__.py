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
    "version": "1.1",
    "author": "Smile",
    "website": 'http://www.smile.fr',
    "category": "Tools",
    "license": 'AGPL-3',
    "description": """
Features
------------------------------------

* Disable auto-subscribe for users
* Activation from user preferences

Usage
------------------------------------

from openerp.addons.smile_followers.tools import AddFollowers, add_followers


@AddFollowers(fields=['restrict_partner_id'])  # by default fields=['partner_id']
class StockMove(models.Model):
    _name = 'stock.move'
    _inherit = ['stock.move', 'mail.thread']


class AccountMove(models.Model):
    _name = 'account.move'
    _inherit = ['account.move', 'mail.thread']

    @api.multi
    @add_followers(fields=['partner_id'])  # by default fields=['partner_id']. In my sample, fields arg is not useful
    def post(self):
        return super(AccountMove, self).post()


Suggestions & Feedback to: isabelle.richard@smile.fr & corentin.pouhet-brunerie@smile.fr
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
