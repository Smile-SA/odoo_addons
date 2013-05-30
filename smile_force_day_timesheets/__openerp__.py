# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2013 Smile (<http://www.smile.fr>).
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
    "name": "Smile Force Day Timesheets",
    "version": "0.1",
    "author": "Smile",
    "website": "http://www.smile.fr",
    "category": "Generic Modules/Project",
    "description": """
        There's one annoying ergonomic issue with the default timesheet
        module: whatever the unit you choose to input your time (hours or
        days), timesheets display them via an HH:MM widget. This module fix
        that by replacing all these widgets by standard float.
        """,
    "summary": "Change default HH:MM widgets on timesheets to simple floats.",
    "depends": [
        'project',
        'hr_timesheet',
        'hr_timesheet_sheet',
        'project_timesheet',
    ],
    "data": [
        # Data & configuration
        'data/res_company.xml',
        # Wizard
        'task_reevaluate_wizard.xml',
        # Views
        'project_view.xml',
        'task_view.xml',
        'analytic_timesheet_view.xml',
        'timesheet_sheet_view.xml',
        'timesheet_task_user_report.xml',
    ],
    "demo": [],
    "test": [],
    "auto_install": False,
    "installable": True,
    "application": True,
}
