# -*- encoding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2016 Smile (<http://www.smile.fr>). All Rights Reserved
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
    "name": "Event Event Calendar",
    "version": "1.0",
    "author": "Smile",
    "website": 'http://www.smile.fr',
    "license": 'AGPL-3',
    "category": "Tools",
    "description": """
Create relationship between event and calendar event
----------------------------------------------------
Add link between event.event and calendar.event.
At event.event creation a new calender.event is created from event.event values.

Suggestions & Feedback to: matthieu.joossen@smile.fr
""",
    "depends": ['event', 'calendar'],
    "data": [
        'views/calendar_view.xml',
    ],
    "demo": [],
    "auto_install": False,
    "installable": True,
    "application": False,
}
