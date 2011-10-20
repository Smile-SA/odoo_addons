# -*- encoding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2011 Smile. All Rights Reserved
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

from osv import osv, fields



class smile_activity_project(osv.osv):
    _name = 'smile.activity.project'

    _columns = {
        'name': fields.char('Name', size=32),
        'value_type': fields.selection([
            ('float', 'Float'),
            ('boolean', 'Boolean'),
            ], 'Value type', select=True, required=True),
        'required': fields.boolean('Required in report'),
        }

    _defaults = {
        'value_type': 'float',
        'required': False,
        }

smile_activity_project()
