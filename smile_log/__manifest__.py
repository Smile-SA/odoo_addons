# -*- coding: utf-8 -*-
# (C) 2021 Smile (<http://www.smile.fr>)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

{
    "name": "Logging in database",
    "version": "3.0",
    "author": "Smile",
    "website": 'http://www.smile.fr',
    "category": "Tools",
    "license": 'AGPL-3',
    "description": """
Logs handler writing to database

Notice

    * Following code will create a log in db with a unique pid per logger:
        from odoo.addons.smile_log.tools import SmileDBLogger
        logger = SmileDBLogger(self._cr.dbname, model'res.partner', self.id, self._uid)
        logger.info(your_message)
""",
    "depends": ['base'],
    "data": [
        "security/smile_log_security.xml",
        "security/ir.model.access.csv",
        "views/smile_log_view.xml",
    ],
    "installable": True,
    "active": True,
}
