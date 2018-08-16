# -*- coding: utf-8 -*-
# (C) 2018 Smile (<http://www.smile.fr>)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

{
    "name": "Talend Jobs",
    "version": "0.1",
    "depends": [
        "mail",
    ],
    "author": "Smile",
    "license": 'AGPL-3',
    "description": """
Features:
* Execute Standalone Jobs
* Display execution logs

Suggestions & Feedback to: corentin.pouhet-brunerie@smile.fr
    """,
    "summary": "",
    "website": "http://www.smile.fr",
    "category": 'Hidden',
    "sequence": 20,
    "data": [
        'security/ir.model.access.csv',
        'views/talend_job_view.xml',
        'views/talend_job_logs_view.xml',
    ],
    "demo": [
        'demo/talend_jobs.xml',
    ],
    "auto_install": True,
    "installable": True,
    "application": False,
}
