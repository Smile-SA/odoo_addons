# -*- encoding: utf-8 -*-
##############################################################################
#
#    Odoo, Open Source Management Solution
#    Copyright (C) 2022 Smile (<https://www.smile.eu>). All Rights Reserved
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

{
    "name": "Smile Cron History",
    "version": "1.0.0",
    "sequence": 100,
    "category": "Tools",
    "author": "Smile",
    "license": 'AGPL-3',
    "website": 'https://www.smile.eu',
    "description": """
This module adds a view allowing to list the calls of the scheduled actions.
(Start/End Date, Status, Error Message)

You can check the "Enable History" box on the scheduled
action you want to track.

You can also configure an email address to
receive an alert when an action fails.
    """,
    "depends": [
        'base',
        'mail',
    ],
    "data": [
        # Data
        'data/ir_cron_data.xml',
        'data/mail_template_data.xml',
        # Security
        'security/groups.xml',
        'security/ir.model.access.csv',
        # Views
        'views/ir_cron_views.xml',
        'views/ir_cron_history_views.xml',
        'views/res_company_views.xml',
    ],
    "auto_install": False,
    "installable": True,
    "application": False,
}
