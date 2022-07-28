# -*- coding: utf-8 -*-
# (C) 2020 Smile (<http://www.smile.fr>)
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl).

{
    'name': 'Customize data',
    'version': '0.1',
    'sequence': 0,
    'author': 'Smile',
    'license': 'LGPL-3',
    'category': 'Tools',
    'description': """
    This application is used to customize and manage the data module
""",
    'website': 'http://www.smile.fr',
    'images': [],
    'depends': [
        'base', 'web'
    ],
    'data': [
        # Security
        'security/group.xml',
        'security/ir.model.access.csv',
        # Views
        'views/assets.xml',
        'views/ir_model_view.xml',
        'views/ir_model_fields_view.xml',
        'views/data_model_menus_view.xml',
        'views/ir_ui_view_views.xml',
        'wizard/export_customization_views.xml',
    ],
    'qweb': [
        'static/src/xml/customize.xml',
    ],
    'installable': True,
    'application': True,
    'auto_install': False,
}
