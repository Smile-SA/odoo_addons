# -*- coding: utf-8 -*-
# (C) 2018 Smile (<http://www.smile.eu>)
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl).
{
    'name': 'Auto Refresh',
    'version': '12.0.1.0.2',
    'depends': [
        'web',
        'bus',
        'mail',
        'base_automation',
    ],
    'author': 'Fisher Yu, Smile',
    'website': '',
    'license': 'AGPL-3',
    'description': """""",
    'category': 'Tools',
    'sequence': 20,
    'data': [
        # Disabling functionality to avoid any leaks for now!
        # 'views/webclient_templates.xml',
    ],
    'qweb': [],
    'auto_install': False,
    'installable': True,
    'application': False,
}
