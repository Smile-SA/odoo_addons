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

{
    "name" : "Smile matrix demo module",
    "version" : "0.9.dev",
    "author" : "Smile",
    "website": 'http://github.com/Smile-SA/smile_openerp_matrix_widget',
    "category" : "Custom",
    "description": "An example module demonstrating the use of the matrix widget.",
    "depends" : [
        'base',
        'smile_matrix_field',
        ],
    "init_xml" : [],
    "update_xml": [
        'smile_activity_view.xml',
        'smile_workload_view.xml',
        'smile_project_view.xml',
        'smile_period_view.xml',
        'smile_profile_view.xml',
        'smile_employee_view.xml',
    ],
    "installable": True,
    "active": False,
}
