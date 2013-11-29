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
    "name": "Smile Payment Cancellation Management",
    "version": "0.1",
    "category": "Generic Modules/Accounting",
    "author": "Smile",
    "website": 'http://www.smile.fr',
    "description": """Payment Cancellation Management

    Instead of deleting account move when you cancel a voucher,
    this module reserves it if this account move was validated, removes it otherwise.

    WARNING: this module is not compatible with account_cancel
    """,
    "depends": ['account_voucher', 'smile_account_reversal'],
    "init_xml": [],
    "update_xml": [
        "view/account_voucher_view.xml",
        "wizard/account_voucher_reversal_view.xml",
    ],
    "demo_xml": [],
    "installable": True,
    "active": False,
}
