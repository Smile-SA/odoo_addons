# -*- encoding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2011 Smile (<http://www.smile.fr>). All Rights Reserved
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
    "name": "Smile Log",
    "version": "1.0",
    "author": "Smile",
    "website": 'http://www.smile.fr',
    "category": "Tools",
    "description": """Logs handler writing to database

Notice

* In your code
import logging
logger = SmileLogger(dbname, model_name, res_id, uid)
logger.info(your_message) will create a log in db with a unique pid per logger

Suggestions & Feedback to: xavier.fernandez@smile.fr, corentin.pouhet-brunerie@smile.fr
""",
    "depends": ['base'],
    "init_xml": [
        "security/smile_log_security.xml",
        "security/ir.model.access.csv",
    ],
    "update_xml": ["smile_log_view.xml", ],
    "demo_xml": [],
    "installable": True,
    "active": False,
}
