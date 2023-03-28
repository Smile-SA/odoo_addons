# Copyright 2023 Smile
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

{
    'name': 'Smile Unreached Invoice',
    'description': """
        Smile Unreached Invoice""",
    'version': '16.0.0.0.0',
    'license': 'AGPL-3',
    'author': 'Smile',
    'website': 'https://www.smile.eu',
    'images': ['static/description/icon.png'],
    'depends': [
        'purchase',
        'smile_account_invoice_generic_wizard',
    ],
    'data': [
        'security/ir.model.access.csv',
        'wizards/smile_unreached_invoice.xml',
    ],
    'demo': [
    ],
    "auto_install": False,
    "installable": True,
    "application": False,
}
