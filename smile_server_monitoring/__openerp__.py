# -*- encoding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2012 Smile (<http://www.smile.fr>). All Rights Reserved
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
    'name': 'Smile Server Monitoring',
    'version': '2.0',
    'category': 'Hidden',
    'description': """Smile Server Monitoring

This module adds the following web page "/web/webclient/status" that displays:
    * OpenERP Server: OK + Databases list
or
    * OpenERP Server: KO + Exception (indicates if is an OpenERP or Postgresql server connection issue)

Configuration step
Add in your configfile server_wide_modules = web,smile_server_monitoring

Suggestions & Feedback to: corentin.pouhet-brunerie@smile.fr, kevin.deldycke@smile.fr, xavier.fernandez@smile.fr
""",
    'author': 'Smile',
    'website': 'http://www.smile.fr',
    'depends': ['web'],
    'auto_install': True,
}
