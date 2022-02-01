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
    "name": "Smile API Rest",
    "version": "1.0.0",
    "sequence": 100,
    "category": "Tools",
    "author": "Smile",
    "license": 'AGPL-3',
    "website": 'https://www.smile.eu',
    "description": """
This module provisions you with an API which allows
you to access models through HTTP requests.
Documentation generate with Swagger OpenAPI
Specification - Version 2.0 (https://swagger.io/specification/v2/)

Suggestions & Feedback to: Corentin POUHET-BRUNERIE & Julien DRECQ
    """,
    "depends": [
        'base',
    ],
    "data": [
        # Security
        'security/groups.xml',
        'security/ir.model.access.csv',
        # Views
        'views/api_rest_version_views.xml',
        'views/api_rest_path_views.xml',
        'views/api_rest_tag_views.xml',
        'views/api_rest_log_views.xml',
        'views/swagger_templates.xml',
    ],
    'assets': {
        'smile_api_rest.assets_swagger': [
            'smile_api_rest/static/lib/swagger-ui-3.38.0/swagger-ui.css',
            'smile_api_rest/static/lib/swagger-ui-3.38.0/swagger-ui-bundle.js',
            'smile_api_rest/static/lib/swagger-ui-3.38.0/swagger-ui-standalone-preset.js',
        ],
    },
    "test": [],
    'installable': True,
    'auto_install': False,
    'application': False,
}
