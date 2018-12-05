# -*- coding: utf-8 -*-
# (C) 2018 Smile (<http://www.smile.eu>)
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl).
{
    'name': 'Auto Refresh',
    'version': '0.1',
    'depends': [
        'web',
        'bus',
        'mail',
        'base_automation',
    ],
    'author': 'Fisher Yu, Smile',
    'website': 'http://www.smile.fr',
    'license': 'AGPL-3',
    'description': """""",
    'category': 'Tools',
    'sequence': 20,
    'data': [
        'views/webclient_templates.xml',
    ],
    'qweb': [],
    'auto_install': True,
    'installable': True,
    'application': False,
}
