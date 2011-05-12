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

import httplib
import subprocess
import time
import traceback

import netsvc
from osv import osv, fields
import tools

class server_object_lines(osv.osv):
    _inherit = 'ir.server.object.lines'

    _columns = {
        'key': fields.char('Key', size=64, required=False),
        'col1': fields.many2one('ir.model.fields', 'Destination', required=False),
    }
server_object_lines()

class talend_job(osv.osv):
    _inherit = 'ir.actions.server'

    def __init__(self, pool, cr):
        super(talend_job, self).__init__(pool, cr)
        item = ('talend_job', 'Talend Job')
        if not item in self._columns['state'].selection:
            self._columns['state'].selection.append(item)

    _columns = {
        'talend_job_export_type': fields.selection([
            ('jar', 'Autonomous Job'),
            ('war', 'Axis WebService (WAR)'),
        ], 'Export Type'),
        'talend_job_project': fields.char('Project', size=50),
        'talend_job_name': fields.char('Job', size=255),
        'talend_job_version': fields.char('Job Version', size=255),
        'talend_job_path': fields.char('Path', size=255),
        'talend_job_context': fields.char('Context', size=50),
        'talend_job_java_xms': fields.char('Xms', size=10),
        'talend_job_java_xmx': fields.char('Xmx', size=10),
        'talend_job_host': fields.char('Host', size=100),
        'talend_job_param_ids': fields.one2many('ir.server.object.lines', 'server_id', 'Parameters'),
    }

    _defaults = {
        'talend_job_export_type': lambda * a: 'jar',
        'talend_job_context': lambda * a: 'Default',
        'talend_job_java_xms': lambda * a: '256M',
        'talend_job_java_xmx': lambda * a: '1024M',
    }

    def _run(self, cr, uid, ids, context=None):
        if isinstance(ids, (int, long)):
            ids = [ids]

        for action in self.browse(cr, uid, ids, context):
            if action.state == 'talend_job':
                params = []
                for param in action.fields_lines:
                    value = param.value
                    if param.type == 'equation':
                        obj_pool = self.pool.get(action.model_id.model)
                        obj = obj_pool.browse(cr, uid, context['active_id'], context=context)
                        cxt = {
                            'context':context,
                            'object': obj,
                            'time':time,
                            'cr': cr,
                            'pool' : self.pool,
                            'uid' : uid,
                        }
                        value = eval(param.value, cxt)
                    params.append("--context_param %s=%s" % (param.key, value))
                if action.talend_job_export_type == 'jar':
                    command = ''
                    if action.talend_job_path:
                        command += 'cd %s && ' % action.talend_job_path.replace(' ', '\ ')
                    command += 'java -Xms%s -Xmx%s -cp classpath.jar: %s.%s_%s.%s --context=%s %s' % (
                        action.talend_job_java_xms,
                        action.talend_job_java_xmx,
                        action.talend_job_project,
                        action.talend_job_name.lower(),
                        action.talend_job_version.replace('.', '_'),
                        action.talend_job_name,
                        action.talend_job_context,
                        ' '.join(params),
                    )
                    subprocess.check_call(command, shell=True)
                elif action.talend_job_export_type == 'war':
                    host = action.talend_job_host
                    if host.startswith('https'):
                        connection = httplib.HTTPSConnection(host.split('/')[2])
                    elif host.startswith('http'):
                        connection = httplib.HTTPConnection(host.split('/')[2])
                    else:
                        connection = httplib.HTTPConnection(host.split('/')[0])
                    url = '/%s_%s/services/%s?method=runJob' % (
                        action.talend_job_name.lower(),
                        action.talend_job_version,
                        action.talend_job_name,
                    )
                    for i, v in enumerate(params):
                        url += '&arg%d=%s' % (i + 1, v)
                    connection.request('GET', url)
                    response = connection.getresponse()
                    if response.status >= 400:
                        raise httplib.HTTPException(response.msg)
            else:
                return super(talend_job, self)._run(cr, uid, ids, context)

        return True
talend_job()
