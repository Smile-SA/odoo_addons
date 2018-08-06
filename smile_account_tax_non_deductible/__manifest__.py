# -*- coding: utf-8 -*-
# (C) 2013 Smile (<http://www.smile.fr>)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

{
    "name": "Non-deductible taxes",
    "version": "0.1",
    "license": 'AGPL-3',
    "depends": ["account"],
    "author": "Smile",
    "description": """Manage non-deductible taxes in French law

Suggestions & Feedback to: corentin.pouhet-brunerie@smile.fr
    """,
    "website": "http://www.smile.fr",
    "category": 'Accounting & Finance',
    "sequence": 32,
    "data": [
        "security/ir.model.access.csv",
        "views/account_invoice_view.xml",
        "views/product_template_view.xml",
        "views/res_company_view.xml",
        "views/res_partner_industry_view.xml",
    ],
    "demo": [],
    'test': [],
    "auto_install": False,
    "installable": True,
    "application": False,
}
