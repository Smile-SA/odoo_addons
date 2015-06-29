# -*- encoding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2010 Smile (<http://www.smile.fr>). All Rights Reserved
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
    "name": "Model Methods",
    "version": "0.1",
    "sequence": 100,
    "category": "Tools",
    "author": "Smile",
    "website": 'http://www.smile.fr',
    "description": """
This module logs model methods and their signatures.
Open the 'wizard method' menu in concfiguration/database structure,
and choose one or multiple models, if no model is defined, all models will be used.
To update records, check update lines field

Suggestions & Feedback to: corentin.pouhet-brunerie@smile.fr
    """,
    "depends": [
        'base',
    ],
    "data": [
        'security/ir.model.access.csv',
        'wizard/wizard_ir_model_method.xml',
        'views/ir_model_view.xml',
    ],
    "test": [],
    'installable': True,
    'auto_install': False,
    'application': False,
}
