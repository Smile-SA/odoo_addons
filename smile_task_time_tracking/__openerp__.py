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
    "name": "Smile Task Time Tracking",
    "version": "0.1",
    "author": "Smile",
    "website": "http://www.smile.fr",
    "category": "Generic Modules/Project",
    "description":
        """
        This module add an history of the time updates applied on project's tasks.
        
        The thing is, I created this module before stumbling upon project.task.history
        objects, which seems to implement more or less the same features as the
        current module (see: http://bazaar.launchpad.net/~openerp/openobject-addons/7.0/annotate/head:/project/project.py#L1339 ).
        Maybe we should extend the later to reduce code duplication.
        """",
    "summary": "Track time updates on project's tasks.",
    "depends": ["project"],
    "data": [
        # Data & configuration
        "security/ir.model.access.csv",
        # Wizards
        'wizard/remaining_time_view.xml',
        # Views
        'task_view.xml',
    ],
    "demo": [],
    "test": [],
    "auto_install": False,
    "installable": True,
    "application": True,
}
