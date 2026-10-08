# -*- coding: utf-8 -*-
# (C) 2026 Smile (<http://www.smile.fr>)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

{
    "name": "Logging in database",
    "version": "20.0.1.0.0",
    "author": "Smile",
    "website": 'http://www.smile.fr',
    "category": "Tools",
    "license": 'AGPL-3',
    "description": """
Logs handler writing to database

Notice

    * Following code will create a log in db with a unique pid per logger:
        from odoo.addons.smile_log.tools import SmileDBLogger
        logger = SmileDBLogger(self.env.cr.dbname, 'res.partner', self.id, self.env.uid)
        logger.info(your_message)
""",
    "depends": ['base'],
    "data": [
        "security/smile_log_security.xml",
        "security/ir.access.csv",
        "views/smile_log_view.xml",
    ],
    "images": ["static/description/banner.gif"],
    "installable": True,
}
