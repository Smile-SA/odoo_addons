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
    "name" : "Checklist",
    "version" : "1.0",
    "author" : "Smile",
    "website": 'http://www.smile.fr',
    "category" : "Tools",
    "description": """

    Concept

    * Give visibility to users filling a form
    
    Principle
    
    A checklist applies to a single object and is composed of:
    1. Tasks
        * List of fields to fill or boolean expressions to respect
        * Server Action executed if the task is completed
    2. Views on which the checklist is visible
    3. Server Action executed if the checklist is completed
        * all action types: email (native or with poweremail), sms, object creation/update, etc
    
    Suggestions & Feedback to: corentin.pouhet-brunerie@smile.fr

    """,
    "depends" : ['base'],
    "init_xml" : ['security/checklist_security.xml'],
    "update_xml": ['checklist_view.xml'],
    "demo_xml" : [],
    "installable": True,
    "active": False,
    "certificate": '',
}
