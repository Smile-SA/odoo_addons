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

    Instead of deleting account move when you cancel a payment,
    this module reserves it if this journal entry was validated,
    removes it otherwise.
    """,
    "depends": [
        'account',
    ],
    "data": [
        "wizard/account_payment_reversal_view.xml",
    ],
    "demo": [],
    "installable": True,
    "active": False,
}
