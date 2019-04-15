# -*- coding: utf-8 -*-
# (C) 2018 Smile (<http://www.smile.fr>)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
{
    'name': "Smile Reconciliation By Line",
    'summary': "Reconcile account statement line by line",
    'author': "Smile SA",
    'website': "http://www.smile.eu",
    'category': 'Accounting',
    'version': '0.1',
    'depends': ['base',
                'account_invoicing',
                ],
    'data': [
        'views/account_bank_statement_view.xml',
    ],
}