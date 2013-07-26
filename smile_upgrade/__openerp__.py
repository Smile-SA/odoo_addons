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
    "name": "Smile Upgrade",
    "version": "0.1",
    "depends": ["base"],
    "author": "Smile",
    "description": """Smile Upgrade

Objectives

    * Allow to upgrade automatically database after code update and server restarting
    * Display a maintenance page instead of home page and kill XML/RPC services during upgrades

Essentials

    * Upgrades structure
        <project_repository>
        `-- upgrades
            |-- 1.1
            |   |-- __init__.py
            |   |-- __upgrade__.py
            |   |-- *.sql
            |   `-- *.yml                   # only for post-load
            |-- 1.2
            |   |-- __init__.py
            |   |-- __upgrade__.py
            |   `-- *.sql
            `-- upgrade.conf

    * Upgrades configuration
        [options]
        version=1.2

    * __upgrade__.py
        Content: dictonary with the following keys:
            * version
            * databases: let's empty if valid for all databases
            * description
            * modules_to_update: modules list to update or install
            * pre-load: list of .sql files
            * post-load: list of .sql or/and .yml files

Suggestions & Feedback to: corentin.pouhet-brunerie@smile.fr
    """,
    "summary": "",
    "website": "http://www.smile.fr",
    "category": 'Hidden',
    "sequence": 20,
    "init_xml": [],
    "update_xml": [],
    'demo_xml': [],
    'test': [],
    "auto_install": True,
    "installable": True,
    "application": False,
}
