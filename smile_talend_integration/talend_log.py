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

from osv import osv, fields

class talend_log(osv.osv):
    _name = 'talend.log'
    _description = 'Talend Log'
    _rec_name = "pid"

    _columns = {
        'moment': fields.datetime('Date'),
        'pid': fields.char('PID', size=20),
        'root_pid': fields.char('Root PID', size=20),
        'father_pid': fields.char('Father PID', size=20),
        'project': fields.char('Project', size=50),
        'job': fields.char('Job', size=255),
        'context': fields.char('Context', size=50),
        'priority': fields.integer('Priority'),
        'type': fields.char('Type', size=255),
        'origin': fields.char('Origin', size=255),
        'message': fields.char('Message', size=255),
        'code': fields.integer('Code'),
    }
talend_log()

class talend_state(osv.osv):
    _name = 'talend.state'
    _description = 'Talend State'
    _rec_name = "pid"

    _columns = {
        'moment': fields.datetime('Date'),
        'pid': fields.char('PID', size=20),
        'father_pid': fields.char('Father PID', size=20),
        'root_pid': fields.char('Root PID', size=20),
        'system_pid': fields.integer('System PID'),
        'project': fields.char('Project', size=50),
        'job': fields.char('Job', size=255),
        'job_repository_id': fields.char('Job Repository ID', size=255),
        'job_version': fields.char('Job Version', size=255),
        'context': fields.char('Context', size=50),
        'origin': fields.char('Origin', size=255),
        'message': fields.char('Message', size=255),
        'duration': fields.integer('Code'),
    }
talend_state()

class talend_flow(osv.osv):
    _name = 'talend.flow'
    _description = 'Talend Flow'
    _rec_name = "pid"

    _columns = {
        'moment': fields.datetime('Date'),
        'pid': fields.char('PID', size=20),
        'father_pid': fields.char('Father PID', size=20),
        'root_pid': fields.char('Root PID', size=20),
        'system_pid': fields.integer('System PID'),
        'project': fields.char('Project', size=50),
        'job': fields.char('Job', size=255),
        'job_repository_id': fields.char('Job Repository ID', size=255),
        'job_version': fields.char('Job Version', size=255),
        'context': fields.char('Context', size=50),
        'origin': fields.char('Origin', size=255),
        'label': fields.char('Label', size=255),
        'count': fields.integer('Count'),
        'reference': fields.integer('Reference'),
        'thresholds': fields.char('Thresholds', size=255),
    }
talend_flow()
