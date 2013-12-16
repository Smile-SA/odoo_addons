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
    "version": "0.2.4",
    "depends": ["mail"],
    "author": "Smile",
    "description": """Smile Base

    * Install and make French the default language for users and partners
    * Remove the scheduled action "Update Notification" which sends companies and users info to OpenERP S.A.
    * Activate access logs for ir.translation object
    * Correct date and time format for French language
    * Force to call unlink method at removal of remote object linked by a fields.many2one with ondelete='cascade'
    * Deduplicate pool._store_function
    * Add BaseModel.bulk_create, BaseModel.store_set_values and BaseModel._compute_store_set
    * Improve BaseModel.import_data method performance
    * Manage uid in Yaml tests
    * Log slow xmlrpc calls
    * Add maintenance tools: IrModel.get_wrong_field_invalidations, db.get_duplicated_indexes, db.get_missing_indexes, db.get_unused_indexes

    Suggestions & Feedback to: corentin.pouhet-brunerie@smile.fr
    """,
    "summary": "",
    "website": "http://www.smile.fr",
    "category": 'Tools',
    "sequence": 20,
    "init_xml": [
        "data/ir_lang.yml",
        "data/ir_cron.xml",
        "security/res_users.yml",
        "security/base_security.xml",
        "security/ir.model.access.csv",
        "view/ir_values_view.xml",
    ],
    "update_xml": [],
    'demo_xml': [],
    'test': [],
    "auto_install": True,
    "installable": True,
    "application": False,
}
