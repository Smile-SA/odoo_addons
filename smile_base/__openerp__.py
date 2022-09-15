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
    "depends": ["mail"],
    "author": "Smile",
    "description": """Smile Base

    * Install and make French the default language
    * Remove the scheduled action "Update Notification" which sends companies and users info to OpenERP S.A.
    * Activate access logs for ir.translation object
    * Correct date and time format for French language
    * Review the menu "Applications"
    * Remove the menu "Update modules" from apps.openerp.com
    * Add sequence and display window actions in IrValues
    * Force to call unlink method at removal of remote object linked by a fields.many2one with ondelete='cascade'
    * Deduplicate pool._store_function
    * Add BaseModel.bulk_create, BaseModel.store_set_values and BaseModel._compute_store_set
    * Improve BaseModel.load method performance
    * Add path to library wkhtmltopdf in table ir_config_parameter (necessary for module report_webkit)

    Suggestions & Feedback to: corentin.pouhet-brunerie@smile.fr
    """,
    "summary": "",
    "website": "http://www.smile.fr",
    "category": 'Tools',
    "sequence": 20,
    "init_xml": [
        "security/base_security.xml",
        "security/res_users.yml",
        "data/ir_lang.yml",
        "data/ir_config_parameter.xml",
        "view/ir_values_view.xml",
        "view/module_view.xml",
    ],
    "update_xml": [],
    'demo_xml': [],
    'test': [],
    "auto_install": True,
    "installable": True,
    "application": False,
}
