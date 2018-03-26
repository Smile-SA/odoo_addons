# -*- encoding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2010 Smile (<http://www.smile.fr>). All Rights Reserved
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
    "name": "Asynchronous Report",
    "version": "0.1",
    "sequence": 100,
    "category": "Tools",
    "author": "Smile",
    "license": 'AGPL-3',
    "website": 'http://www.smile.fr',
    "description": """
Features

    * Allows to launch report generation in background
    * Notify users from instant messaging

Suggestions & Feedback to: corentin.pouhet-brunerie@smile.fr
    """,
    "depends": [
        "mail",
    ],
    "data": [
        "views/ir_actions_report.xml",
    ],
    'installable': True,
    'auto_install': True,
    'application': False,
}
