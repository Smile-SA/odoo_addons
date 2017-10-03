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
    "name": "Discount Contract",
    "version": "0.1",
    "depends": [
        "account",
    ],
    "author": "Smile",
    "license": 'AGPL-3',
    "description": """
Discount Contract
=================

Suggestions & Feedback to: victor.bahl@smile.fr &
    corentin.pouhet-brunerie@smile.fr
    """,
    "website": "http://www.smile.fr",
    'category': 'Accounting',
    "sequence": 0,
    "data": [
        "security/ir.model.access.csv",
        "security/discount_contract_security.xml",

        "views/discount_contract_line_view.xml",
        "views/discount_contract_view.xml",
        "views/discount_contract_close_reason_view.xml",
        "views/discount_contract_rule_view.xml",
        "views/discount_contract_rule_slice_view.xml",
        "views/discount_contract_template_view.xml",
        "views/account_invoice_view.xml",
        "views/menus.xml",

        "report/discount_contract_report.xml",

        "data/ir_sequence_data.xml",
        "data/ir_cron_data.xml",
        "data/discount_contract_close_reason_data.xml",
        "data/mail_template_data.xml",
    ],
    "demo": [
        "demo/discount_contract_demo.xml",
    ],
    "auto_install": False,
    "installable": True,
    "application": False,
}
