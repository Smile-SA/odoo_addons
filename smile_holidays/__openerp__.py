# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2015 Smile (<http://www.smile.fr>).
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

{
    'name': "Smile - Holidays",
    'summary':
    """
        Links holidays areas to a department
    """,
    'description':
    """

    """,
    'author': "Smile",
    'category': 'French Localization',
    'version': '0.1',
    'depends': [
        'l10n_fr_department'
    ],
    'data': [
        # Security
        'security/security.xml',
        'security/ir.model.access.csv',

        # Data
        'data/res.holidays.area.csv',
        # INFO: areas are based on this link: http://vacances-scolaires.education/departement/
        'data/res.holidays.attribution.csv',

        # Views
        'views/res_holidays_view.xml',
    ],
    'demo': [
        'demo/res_holidays_demo.xml',
    ],
}
