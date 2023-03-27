# -*- coding: utf-8 -*-
# (C) 2022 Smile (<https://www.smile.eu>)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

{
    'name': 'Smile OAuth',
    'version': '14.0.1.0.0',
    'sequence': 0,
    'author': 'Smile',
    'license': 'AGPL-3',
    'category': '',
    'description': """
    This module manage Authorization Flow and
    Authorization Flow With PKCE for Oauth provider.
""",
    'website': 'https://www.smile.eu',
    'images': [],
    'depends': [
        'auth_oauth',
    ],
    'data': [
        # views
        'views/auth_oauth_views.xml',
    ],
    'installable': True,
    'application': False,
    'auto_install': False,
}
