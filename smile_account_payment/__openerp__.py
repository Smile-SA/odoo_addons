# -*- encoding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2010 Smile (<http://www.smile.fr>). All Rights Reserved
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
    "name": "Smile Account Payment",
    "version": "0.1",
    "category": "Generic Modules/Accounting",
    "author": "Smile",
    "website": 'http://www.smile.fr',
    "description": """Smile Account Payment

Changes from editor module:
1. A payment order doesn't contain lines anymore, it links to vouchers
2. The validation of a payment order doesn't generate bank statement lines but validates vouchers
3. The cancellation of a payment order cancel vouchers
    """,
    "depends": ['account_voucher'],
    "init_xml": [],
    "update_xml": [
        "security/account_payment_security.xml",
        "security/ir.model.access.csv",
        "data/account_payment_sequence.xml",
        "workflow/account_payment_workflow.xml",
        "view/account_payment_view.xml",
        "view/account_invoice_view.xml",
        "view/res_company_view.xml",
        "view/account_voucher_view.xml",
    ],
    "demo_xml": [],
    "installable": True,
    "active": False,
}
