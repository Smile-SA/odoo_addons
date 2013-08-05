# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2012 Smile (<http://www.smile.fr>).
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
    "name": "Smile Colored widget",
    "category": "Hidden",
    "description": """Add new widget 'colored':
<field name="field_name" widget="colored" attrs="{'colored':{'blue':'&gt;200','red':'&lt;200'}}"/> in form and list view""",
    "version": "1.0",
    "depends": ['web'],
    'auto_install': False,
    'js': [
        'static/src/js/colored.js'
    ],
}
