# -*- encoding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2012 Smile (<http://www.smile.fr>). All Rights Reserved
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
    "name": "Assets Management",
    "version": "0.2",
    "depends": ["smile_base", "account", "smile_report_utils"],
    "author": "Smile",
    "description": """Financial and accounting asset management

This module allows to manage:
* assets and categories
* decomposable assets
* amortizations (ie periodic depreciations) and depreciations (exceptional)
* accounting and fiscal depreciation methods (v0.2)
* assets sale/scrapping
* out of heritage
* asset decomposition
* asset modification
* reporting (v0.2)
* transfer depreciation in amortization (v0.2 - French law)

WARNING: This module is not compatible with account_asset, so uninstall it before installing this one.

Suggestions & Feedback to: corentin.pouhet-brunerie@smile.fr
    """,
    "website": "http://www.smile.fr",
    "category": "Accounting & Finance",
    "sequence": 32,
    "init_xml": [
        "security/account_asset_security.xml",
        "security/ir.model.access.csv",
        "data/account_asset_sequence.xml",
        "data/account_asset_depreciation_method_data.xml",
    ],
    "update_xml": [
        "view/account_asset_menu.xml",
        "view/account_asset_category_view.xml",
        "view/account_asset_depreciation_line_view.xml",
        "view/account_asset_depreciation_method_view.xml",
        "view/account_asset_view.xml",
        "view/account_asset_history_view.xml",
        "view/account_invoice_view.xml",
        "view/account_view.xml",
        "view/res_company_view.xml",
        "wizard/account_asset_split_wizard_view.xml",
        "report/account_asset_report_header.xml",
        "report/account_asset_report.xml",
    ],
    "demo_xml": [
        "demo/account_demo.xml",
        "demo/account_tax_demo.xml",
        "demo/account_asset_category_demo.xml",
        "demo/account_asset_demo.xml",
        "demo/res_company_demo.xml",
    ],
    'test': [
        "test/run_tests.yml",
        "test/account_asset_test.yml",
        "test/account_asset_depreciation_line_test.yml",
        "test/account_asset_post_test.yml",
        "test/account_asset_account_changes_test.yml",
        "test/account_asset_history_test.yml",
        "test/account_asset_cancel_purchase_test.yml",
        "test/account_asset_copy_test.yml",
        "test/account_asset_split_test.yml",
        "test/account_asset_modify_test.yml",
        "test/account_asset_sale_test.yml",
        "test/account_asset_cancel_sale_test.yml",
        "test/account_asset_scrapping_test.yml",
        "test/account_invoice_line_test.yml",
        "test/account_period_test.yml",
        "test/account_fiscalyear_test.yml",
    ],
    "auto_install": False,
    "installable": True,
    "application": True,
}
