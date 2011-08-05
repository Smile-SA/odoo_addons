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

import datetime

from osv import osv, fields


class smile_project(osv.osv):
    _name = 'smile.project'

    _columns = {
        'name': fields.char('Name', size=32),
        'start_date': fields.date('Start', required=True),
        'end_date': fields.date('End', required=True),
        'line_ids': fields.one2many('smile.project.line', 'project_id', "Project lines"),
        }

    _defaults = {
        'start_date': datetime.datetime.today().strftime('%Y-%m-%d'),
        'end_date': (datetime.datetime.today() + datetime.timedelta(days=7)).strftime('%Y-%m-%d'),
        }

    def matrix(self, cr, uid, ids, context=None):
        if len(ids) >1:
            raise osv.except_osv('Error', 'len(ids) !=1')
        project = self.browse(cr, uid, ids[0], context)

        vals = {}
        for month in self.pool.get('smile.matrix')._get_project_months(project):
            month_str = self.pool.get('smile.matrix')._month_to_str(month)
            for line in project.line_ids:
                vals['line_%s_%s' % (line.id, month_str)] = line.price

        new_context = context.copy()
        new_context['project_id'] = ids[0]
        matrix_id = self.pool.get('smile.matrix').create(cr, uid, vals, new_context)
        return {
                'name': "%s matrix" % (project.name,),
                'type': 'ir.actions.act_window',
                'res_model': 'smile.matrix',
                'res_id': matrix_id,
                'view_mode': 'form',
                'view_type': 'form',
                'context': new_context,
                'target': 'new',
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
