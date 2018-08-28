# -*- coding: utf-8 -*-
# Copyright (C) 2013-Today OpenSur.
# (C) 2015 Smile (<http://www.smile.fr>)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

{
    'name': 'Smile Blogs private',
    'category': 'Website',
    'website': 'https://www.smile.fr',
    'summary': 'Blogs and post private access',
    'version': '1.00',
    'description': """
OpenERP Blog Private
====================
Add feature to have private blogs and post, visible only for certain security groups
Origine from https://github.com/OpenSur/Odoo_addons#8.0 convert to > 10
        """,
    'author': 'OpenSur, Smile SA',
    'license': 'AGPL-3',
    'depends': ['website_blog'],
    'data': [
        'data/access_rules.xml',
        'views/website_blog_private_views.xml'
    ],
    'demo': [
    ],
    'test': [
    ],
    'qweb': [
    ],
    'installable': True,
    'application': True,
}
