# -*- encoding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2011 Smile (<http://www.smile.fr>). All Rights Reserved
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
    "name": "Access Control",
    "version": "1.0",
    "author": "Smile",
    "website": 'http://www.smile.fr',
    "license": 'AGPL-3',
    "category": "Tools",
    "description": """
Manage users thanks to user profiles
------------------------------------

This is a new way to manage your users' rights :
you can manage users by functional profiles.

Basically, a « profile » is a fictive user (res.users) tagged as a profile.
It means that like before (with the basic rules of OpenERP) you can add groups to your profile.
You can associate a profile to your user. Or in an other way, you can add users by profile.
You can also set the fields which are private per user or global for all users.
You have choice to update or not in write mode for associated users,  with field 'Update users' in profiles.

NB : to test your profile, you need to set him as « active », which will be disabled afterwards at the next update.

Suggestions & Feedback to: corentin.pouhet-brunerie@smile.fr & matthieu.choplin@smile.fr
""",
    "depends": ['base'],
    "data": [
        "views/res_users_view.xml",
        "data/res_users_data.xml",
        "views/res_groups_view.xml",
        'views/res_company_view.xml',
    ],
    "demo": [],
    "installable": True,
    "active": False,
}
