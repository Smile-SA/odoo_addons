# -*- coding: utf-8 -*-
# (C) 2014 Smile (<http://www.smile.fr>)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

{
    "name": "Automated Actions",
    "version": "0.1",
    "depends": [
        "base_automation",
        "smile_log",
    ],
    "author": "Smile",
    "license": 'AGPL-3',
    "description": """
This module extends base_automation.

Additional features

    * Extend automated actions to:
        * Trigger on other method
        * Limit executions per record
        * Log executions for actions not on timed condition
        * Raise customized exceptions
        * Categorize them
    * Extend server actions to:
        * Force execution even if records list is empty
        * Execute in asynchronous mode

Suggestions & Feedback to: corentin.pouhet-brunerie@smile.fr
    """,
    "summary": "",
    "website": "http://www.smile.fr",
    "category": 'Tools',
    "sequence": 20,
    "data": [
        "security/ir.model.access.csv",
        "data/ir_cron_data.xml",
        "views/ir_actions.xml",
        "views/ir_model_methods_view.xml",
        "views/base_automation_view.xml",
    ],
    "auto_install": False,
    "installable": True,
    "application": False,
}
