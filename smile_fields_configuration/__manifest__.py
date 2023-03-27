# -*- coding: utf-8 -*-
# (C) 2021 Smile (<http://www.smile.fr>)
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl).

{
    "name": "Smile Fields Configuration",
    "version": "14.0.1.0.0",
    "sequence": 100,
    "category": "Tools",
    "author": "Smile",
    "license": 'LGPL-3',
    "description": """
        Add configuration on field to manage referencial.
    """,
    "depends": [
        'web',
    ],
    "data": [
        # Security
        'security/ir.model.access.csv',
        # Views
        'views/assets.xml',
        'views/ir_model_fields_configuration_views.xml',
        'views/ir_model_fields_views.xml',
        'views/ir_referencial_views.xml',
        'views/collected_pivot_model_views.xml',
    ],
    'installable': True,
    'auto_install': False,
    'application': False,
}
