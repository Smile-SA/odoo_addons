# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2014-2016 Smile (<http://www.smile.fr>).
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
    "name": "Security Advisory",
    "version": "1.0",
    "depends": ['smile_scm'],
    "author": "Smile",
    "license": 'AGPL-3',
    "summary": "",
    "description": """
Security Advisory
=================

Suggestions & Feedback to: corentin.pouhet-brunerie@smile.fr
    """,
    "summary": "",
    "website": "http://www.smile.fr",
    "category": 'Tools',
    "sequence": 20,
    "data": [
        "security/ir.model.access.csv",
        "views/scm_repository_branch_view.xml",
        "views/scm_security_advisory_view.xml",
    ],
    "demo": [],
    "qweb": [],
    "auto_install": False,
    "installable": True,
    "application": False,
    "external_dependencies": {
        'python': ['docker', 'requests'],
    },
}
