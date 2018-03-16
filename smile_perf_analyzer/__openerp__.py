# -*- encoding: utf-8 -*-
##############################################################################
#
#    odoo, Open Source Management Solution
#    Copyright (C) 2017 Smile (<http://www.smile.fr>). All Rights Reserved
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
    "name": "Performance Analyzer",
    "version": "0.1",
    "depends": [
        "decimal_precision",
        "smile_filtered_from_domain",
    ],
    "author": "Smile",
    "license": 'AGPL-3',
    "description": """
Performance Analyzer
====================

Features
--------

This module log in function of logging rules:
* each JSON-RPC / XML-RPC call linked to a model: db, datetime, model, method, user, total time, db time, args, result
* Python method profiling
* SQL queries stats

A logging rule is defined directly via the user interface
(menu: Settings > Technical > Performance > Rules)
and it's applied without restarting Odoo server.

To hide the database *_perf created at installation, add "dbfilter = (?!.*_perf$)" in your config file.

Suggestions & Feedback to: isabelle.richard@smile.fr & corentin.pouhet-brunerie@smile.fr
    """,
    "website": "http://www.smile.fr",
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
