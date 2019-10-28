# -*- coding: utf-8 -*-
# (C) 2011 Smile (<http://www.smile.fr>)
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl).

{
    "name": "Access Control",
    "version": "1.0",
    "author": "Smile",
    "license": 'LGPL-3',
    "category": "Tools",
    "description": """
Manage users thanks to user profiles
------------------------------------

This is a new way to manage your users' rights :
you can manage users by functional profiles.

Basically, a « profile » is a fictive user (res.users) tagged as a profile.

It means that like before (with the basic rules of Odoo),
you can add groups to your profile.

You can associate a profile to your user. Or in an other way,
you can add users by profile.

You can also set the fields which are private per user or global for all users.

You have choice to update or not in write mode for associated users,
with field 'Update users' in profiles.

NB : to test your profile, you need to set him as « active »,
which will be disabled afterwards at the next update.

Suggestions & Feedback to: corentin.pouhet-brunerie@smile.fr &
matthieu.choplin@smile.fr
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
