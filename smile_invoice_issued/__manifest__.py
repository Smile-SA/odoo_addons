# Copyright 2023 Smile
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

{
    'name': 'Smile Invoice Issued',
    'description': """
        Smile Invoice Issued""",
    'version': '16.0.0.0.0',
    'license': 'AGPL-3',
    'author': 'Smile',
    'website': 'https://www.smile.eu',
    'images': ['static/description/icon.png'],
    'depends': [
        'sale_management',
        'smile_account_invoice_generic_wizard',
    ],
    'data': [
        'security/ir.model.access.csv',
        'wizards/smile_invoice_issued.xml',
    ],
    'demo': [
    ],
    "auto_install": False,
    "installable": True,
    "application": False,
}
