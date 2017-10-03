# -*- coding: utf-8 -*-

{
    'name': "Smile Account Export",
    'summary': "",
    'description': "",
    'author': "Smile",
    'category': 'Accounting',
    'version': '1.0',
    'depends': ['account'],
    'data': [
        'security/account_export_security.xml',
        'security/ir.model.access.csv',

        'views/account_move_line_view.xml',
        'views/account_export_view.xml',
        'views/account_export_template_view.xml',
        'views/menus.xml',
    ],
    'installable': True,
    'external_dependencies': {
        'python': [
            'unicodecsv',
        ],
    },
}
