# -*- encoding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2015 Smile (<http://www.smile.fr>). All Rights Reserved
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
    'name': 'Smile Account Followup',
    'version': '1.0',
    'depends': [
        'account',
        'smile_access_control',
    ],
    'author': 'Smile',
    'description': """
            # Manage Customers Recovery: adds reminder actions & reminder levels. Reminder actions can be associated to invoices and thus give them a reminder level. 
    """,
    'summary': '',
    'website': 'http://www.smile.fr',
    'category': 'Account',
    'sequence': 10,
    'data': [
        'security/recovery_security.xml',
        'security/ir.model.access.csv',
        'data/level_type_data.xml',
        'views/action_reminder_view.xml',
        'views/account_view.xml',
        'views/wizard_account_followup_view.xml',
        'views/wizard_create_action_reminder_view.xml',
        'views/report_unpaid_invoice.xml',
        'views/account_followup_report.xml',
    ],
    'test': [],
    'auto_install': False,
    'installable': True,
    'application': False,
}
