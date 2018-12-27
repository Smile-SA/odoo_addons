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
    "name": "Docker",
    "version": "1.0",
    "depends": ['smile_base'],
    "author": "Smile",
    "license": 'AGPL-3',
    "summary": "",
    "description": """""",
    "summary": "",
    "website": "http://www.smile.fr",
    "category": 'Tools',
    "sequence": 20,
    "data": [
        # Security
        "security/docker_security.xml",
        "security/ir.model.access.csv",

        # Views
        "views/docker_host_view.xml",
        "views/docker_image_view.xml",
        "views/docker_registry_view.xml",
        "wizard/docker_host_stats_view.xml",
        "wizard/docker_registry_cleaning_view.xml",

        # Data
        "data/docker_host.xml",
        "data/docker_registry.xml",
        "data/ir_cron.xml",
    ],
    "demo": [
        # "demo/docker_image.xml",
    ],
    "qweb": [],
    "auto_install": False,
    "installable": True,
    "application": False,
    "external_dependencies": {
        'python': ['docker', 'requests'],
    },
}
