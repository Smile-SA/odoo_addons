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
    "name": "Grouped Payment Management",
    "version": "0.1",
    "depends": ["account_voucher"],
    "author": "Smile",
    "description": """Grouped Payment Management

TODO:
* Créer une vue des factures "progress_paid" regroupées par date_due puis partner_id
* Créer une action planifiée lançant la génération des paiements groupés

Suggestions & Feedback to: corentin.pouhet-brunerie@smile.fr
    """,
    "website": "http://www.smile.fr",
    "category": "Accounting & Finance",
    "sequence": 32,
    "init_xml": [
        'data/ir_cron_data.xml',
        'data/account_payment_mode_data.xml',
        'security/ir.model.access.csv',
        'workflow/account_invoice_workflow.xml',
    ],
    "update_xml": [
        'view/account_invoice_view.xml',
        'view/account_payment_mode_view.xml',
        'view/res_partner_view.xml',
    ],
    "demo_xml": [
        'demo/account_payment_mode_demo.xml',
    ],
    'test': [],
    "auto_install": False,
    "installable": True,
    "application": False,
}
