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
from matrix_field import matrix, matrix_read_patch, matrix_write_patch



class smile_activity_workload(osv.osv):
    _name = 'smile.activity.workload'

    _columns = {
        'name': fields.char('Name', size=32),
        'project_id': fields.many2one('smile.activity.project', "Project", required=True),
        'start_date': fields.related('project_id', 'start_date', type='date', string="Start date", readonly=True),
        'end_date': fields.related('project_id', 'end_date', type='date', string="End date", readonly=True),
        'line_ids': fields.one2many('smile.activity.workload.line', 'workload_id', "Workload lines"),
        'matrix_line_ids': matrix(
            line_property='line_ids',
            line_type='smile.activity.workload.line',
            line_inverse_property='workload_id',
            cell_property='cell_ids',
            cell_type='smile.activity.workload.cell',
            date_range_property='project_id',
            date_format='%m/%y',
            resource_type='smile.activity.profile',
            line_resource_property='profile_id',
            css_class=['workload'],
            experimental_slider=True,
            string="Workload lines",
            readonly=False,
            ),
        }


    ## Native methods

    @matrix_read_patch
    def read(self, cr, uid, ids, fields=None, context=None, load='_classic_read'):
        return super(smile_activity_workload, self).read(cr, uid, ids, fields, context, load)

    @matrix_write_patch
    def write(self, cr, uid, ids, vals, context=None):
        return super(smile_activity_workload, self).write(cr, uid, ids, vals, context)

smile_activity_workload()



class smile_activity_workload_line(osv.osv):
    _name = 'smile.activity.workload.line'

    _columns = {
        'name': fields.related('profile_id', 'name', type='char', string='Profile name', size=32, readonly=True),
        'workload_id': fields.many2one('smile.activity.workload', "Workload", required=True, ondelete='cascade'),
        'profile_id': fields.many2one('smile.activity.profile', "Profile", required=True),
        'employee_id': fields.many2one('smile.activity.employee', "Employee", required=False),
        }

smile_activity_workload_line()
