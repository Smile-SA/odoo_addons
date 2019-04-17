# -*- coding: utf-8 -*-
# (C) 2019 Smile (<http://www.smile.fr>)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

{
    "name": "Assets Management",
    "version": "0.2",
    "license": 'AGPL-3',
    "depends": [
        "uom",
        "account",
        "smile_api_depends_filter",
        "l10n_generic_coa",
    ],
    "author": "Smile",
    "description": """Financial and accounting asset management

This module allows to manage:
* assets and categories
* amortizations (ie periodic depreciations) and depreciations (exceptional)
* accounting and fiscal depreciation methods
* assets sale/scrapping
* out of heritage
* asset decomposition
* asset modification
* reporting
* transfer depreciation in amortization (French law)

WARNING: This module is not compatible with account_asset, so uninstall it
before installing this one.

Suggestions & Feedback to: Corentin Pouhet-Brunerie
    """,
    "website": "http://www.smile.fr",
    "category": "Accounting & Finance",
    "sequence": 32,
    "data": [
        "security/account_asset_security.xml",
        "security/ir.model.access.csv",

        "data/account_asset_depreciation_methods.xml",
        "data/account_asset_sequence.xml",
        "data/report_paperformat.xml",

        "report/account_asset_depreciations_report.xml",
        "report/account_asset_fiscal_deductions_report.xml",
        "report/account_asset_in_progress_report.xml",
        "report/account_asset_report.xml",
        "report/account_asset_sales_report.xml",

        "views/account_asset_depreciation_method_view.xml",
        "views/account_asset_category_view.xml",
        "views/account_asset_depreciation_line_view.xml",
        "views/account_asset_history_view.xml",
        "views/account_asset_asset_view.xml",
        "views/account_invoice_line_view.xml",
        "views/res_company_view.xml",
        "views/menus.xml",
        "views/webclient_template.xml",

        "wizard/account_asset_split_wizard_view.xml",
        "wizard/account_asset_report_common_view.xml",
        "wizard/account_asset_depreciations_report_view.xml",
        "wizard/account_asset_fiscal_deductions_report_view.xml",
        "wizard/account_asset_in_progress_view.xml",
        "wizard/account_asset_report_view.xml",
        "wizard/account_asset_sales_report_view.xml",
    ],
    "demo": [],
    'qweb': [
        'static/src/xml/account_asset.xml',
    ],
    'test': [],
    "auto_install": False,
    "installable": True,
    "application": False,
}
