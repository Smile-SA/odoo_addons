# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2014 Smile (<http://www.smile.fr>).
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
    "name": "smile_csv2xml_converter",
    "version": "0.1",
    "depends": ['base'],
    "author": "Manh",
    "description": """
    This module allows users to generate an xml file based on the selected object or an uploaded csv file.
    They can choose what fields are going to be generated. The data are filled with the csv file
    Once the the model is generated, you can download it.

    """,
    "summary": "",
    "website": "http://www.smile.fr",
    "category": 'Tools',
    "sequence": 20,
    "data": ['security/ir.model.access.csv',
             'wizard/wizard_upload_view.xml',
             'views/smile_csv2xml_converter_view.xml',
             ],
    "auto_install": False,
    "installable": True,
    "application": False,
}
