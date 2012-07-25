# -*- encoding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2011 Smile (<http: //www.smile.fr>). All Rights Reserved
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
#    along with this program.  If not, see <http: //www.gnu.org/licenses/>.
#
##############################################################################

{
    "name": "Smile dir scanner",
    "version": "0.1",
    "category": "Tools",
    "author": "Smile",
    "website": 'http: //www.smile.fr',
    "description": """
DEVELOPMENT IN PROGRESS

- Define a template: will scan the specified directory for any file matching the corresponding regular expression
- Keep track of the found files

+ Used in combination with smile_action_trigger, found files can easily be imported:
define a trigger on the creation of an smile_dir_scanner.file and link it to a server
action calling the import method that should deal with the file

    """,
    "depends": ['base'],
    "init_xml": [],
    "update_xml": [
        'security/smile_dir_scanner_security.xml',
        'smile_dir_scanner_view.xml',
    ],
    "demo_xml": [
    ],
    "installable": True,
    "active": False,
    "certificate": '',
}
