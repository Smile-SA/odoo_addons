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
    "name": "Continuous Delivery",
    "version": "1.0",
    "depends": [
        "smile_ci",
    ],
    "author": "Smile",
    "license": 'AGPL-3',
    "summary": "Deploy your Odoo app",
    "description": """
Continuous Delivery
===================

Features

    # Deploy your Odoo app thanks to Ansible

Suggestions & Feedback to: corentin.pouhet-brunerie@smile.fr
    """,
    "summary": "Deploy",
    "website": "http://www.smile.fr",
    "category": 'Tools',
    "sequence": 20,
    "data": [
        "data/ansible_inventory_type.xml",
        "data/ansible_role.xml",
        "data/docker_image.xml",
        "data/scm_version_package.yml",

        "security/cd_security.xml",
        "security/ir.model.access.csv",

        "views/ansible_deployment_view.xml",
        "views/ansible_inventory_type_view.xml",
        "views/ansible_role_view.xml",
        "views/docker_image_view.xml",
        "views/scm_repository_branch_view.xml",
        "views/scm_repository_branch_build_view.xml",
        "views/scm_menu.xml",
    ],
    "demo": [],
    "qweb": [],
    "auto_install": False,
    "installable": True,
    "application": False,
}
