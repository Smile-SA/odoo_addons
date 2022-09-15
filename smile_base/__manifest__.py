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
    "name": "Smile Base",
    "version": "0.2.3",
    "depends": [
        'fetchmail',
        'web_editor',
        'web_kanban',
        'web_planner',
    ],
    "author": "Smile",
    "license": 'AGPL-3',
    "description": """""",
    "summary": "",
    "website": "http://www.smile.fr",
    "category": 'Tools',
    "sequence": 20,
    "data": [
        "security/base_security.xml",
        "security/res_users.yml",
        "data/act_actions_window.yml",
        "data/ir_lang.yml",
        "data/im_odoo_support.yml",
        "data/ir_module_menu.yml",
        "data/warning_data.xml",
        "views/ir_values_view.xml",
        "views/template.xml",
    ],
    "qweb": [
        "static/src/xml/base.xml",
        "static/src/xml/env_ribbon.xml",
    ],
    "auto_install": True,
    "installable": True,
    "application": False,
}
