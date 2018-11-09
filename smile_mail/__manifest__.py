# -*- encoding: utf-8 -*-
##############################################################################
#
#    odoo, Open Source Management Solution
#    Copyright (C) 2017 Smile (<http://www.smile.fr>). All Rights Reserved
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
    "name": "Mail - QWeb Editor",
    "version": "0.1",
    "category": "Discuss",
    "depends": [
        "mass_mailing",
    ],
    "author": "Smile",
    "license": 'AGPL-3',
    "description": """
Mail - QWeb Editor
==================

Replace native editor by QWeb editor for the body of mail template and mail composer.

    """,
    "website": "http://www.smile.fr",
    "sequence": 0,
    "data": [
        "views/mail_template_views.xml",
        "wizard/mail_compose_message_view.xml",
    ],
    "demo": [],
    "auto_install": True,
    "installable": True,
    "application": False,
}
