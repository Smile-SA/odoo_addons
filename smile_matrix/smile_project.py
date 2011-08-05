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


class smile_project(osv.osv):
    _name = 'smile.project'

    _columns = {
        'name': fields.char('Name', size=32),
        'line_ids': fields.one2many('smile.project.line', 'project_id', "Project lines"),
        }

smile_project()


class smile_project_line(osv.osv):
    _name = 'smile.project.line'

    _columns = {
        'name': fields.char('Name', size=32, required=True),
        'price': fields.float('Price'),
        'project_id': fields.many2one('smile.project', "Project", required=True, ondelete='cascade'),
        }

smile_project_line()
