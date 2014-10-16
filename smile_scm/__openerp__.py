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

{
    "name": "Source Code Management",
    "version": "0.1",
    "depends": ["mail"],
    "author": "Smile",
    "description": """Source Code Management

    Suggestions & Feedback to: corentin.pouhet-brunerie@smile.fr
    """,
    "summary": "",
    "website": "http://www.smile.fr",
    "category": 'Tools',
    "sequence": 20,
    "data": [
        "security/scm_security.xml",
        "security/ir.model.access.csv",
        "data/scm.vcs.csv",
        "data/scm.version.csv",
        "data/scm.repository.tag.csv",
        "views/scm_vcs_view.xml",
        "views/scm_version_view.xml",
        "views/scm_repository_tag_view.xml",
        "views/scm_repository_view.xml",
        "views/scm_repository_branch_view.xml",
    ],
    "auto_install": False,
    "installable": True,
    "application": False,
}
