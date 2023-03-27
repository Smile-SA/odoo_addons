# -*- coding: utf-8 -*-
# (C) 2018 Smile (<https://www.smile.eu>)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

{
    "name": "Performance Analyzer",
    "version": "14.0.1.0.0",
    "depends": [
        "base",
    ],
    "author": "Smile",
    "license": 'AGPL-3',
    "description": """
Performance Analyzer
====================

Features
--------

This module log in function of logging rules:
* each JSON-RPC / XML-RPC call linked to a model:
  db, datetime, model, method, user, total time, db time, args, result
* Python method profiling
* SQL queries stats

A logging rule is defined directly via the user interface
(menu: Settings > Technical > Performance > Rules)
and it's applied without restarting Odoo server.

To hide the database *_perf created at installation,
add "dbfilter = (?!.*_perf$)" in your config file.
    """,
    "website": "",
    'category': 'Tools',
    "sequence": 0,
    "data": [
        "security/ir.model.access.csv",
        "data/decimal.precision.csv",
        "views/perf_rule_view.xml",
        "views/perf_log_view.xml",
    ],
    "demo": [
        "demo/ir.logging.perf.rule.csv",
    ],
    "auto_install": False,
    "installable": True,
    "application": False,
}
