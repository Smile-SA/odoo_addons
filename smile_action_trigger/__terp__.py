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
    "name" : "Server Actions R* Trigger Rules Engine (aka Sartre)",
    "version" : "3.1",
    "author" : "Smile",
    "website": 'http://www.smile.fr',
    "category" : "Tools",
    "description": """

    Concept
    
    * Give to functional users the possibility to create trigger rules for server actions
    * Make easier to technical users the application maintenance and scalability
    
    Principle
    
    A rule applies to a single object and is composed of:
    1. Triggers on
        * object creation
        * object update
        * object deletion
        * object date (creation date, last update date or another date)
        * object function field recalculation (thus you can trigger the calculation of function fields on cascade)
        * object methods (with an argument named id or ids in its signature)
        * user login
    2. Conditions
        * operators: you can create your own operators (which apply to current or old field value)
        * value age: current or old values if the rule trigger is the object update
    3. Server Actions
        * all action types: email (native or with poweremail), sms, object creation/update, etc
		* run each action once per instance or once for all instances
    
    Suggestions & Feedback to: corentin.pouhet-brunerie@smile.fr

    """,
    "depends" : ['base'],
    "init_xml" : ['security/sartre_security.xml', 'ir_cron_data.xml'],
    "update_xml": ['ir.xml', 'sartre_view.xml', 'sartre_data.xml'],
    "demo_xml" : ['sartre_demo.xml'],
    "installable": True,
    "active": False,
    "certificate": '',
}
