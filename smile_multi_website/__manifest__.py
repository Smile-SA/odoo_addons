# -*- coding: utf-8 -*-
# (C) 2015 Smile (<http://www.smile.fr>)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

{
    'name': 'Smile Multi Website',
    'category': 'Website',
    'website': 'https://www.smile.fr',
    'summary': 'Add website configuration menu',
    'version': '1.00',
    'description': """
Smile Multi Website
====================
Add access to the website model with a new menu for the community version.
It already exists in enterprise version.
Check the readme for the configuration and usage.

Suggestions & Feedback to: Jonathan Dhosy
        """,
    'author': 'Smile SA',
    'license': 'AGPL-3',
    'depends': ['website'],
    'data': ['views/website.xml'],
    'demo': [
    ],
    'test': [
    ],
    'qweb': [
    ],
    'installable': True,
    'application': True,
}
