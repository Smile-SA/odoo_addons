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

import time

from openerp.exceptions import DeferredException as OpenERPException
from web.common import http as openerpweb
from web.controllers.main import WebClient


def _get_exception_message(e):
    msg = e
    if isinstance(e, OpenERPException):
        msg = e.message
    if msg == 'Connection refused':
        msg = 'Connection to the OpenERP server failed'
    elif 'psycopg2.connect' in msg:
        msg = 'Connection to the PostgreSQL server failed<br/>%s' % msg
    return msg


@openerpweb.httprequest
def status(self, req):
    msg = "OpenERP Server: "
    try:
        db_list = req.session.proxy('db').list()
        msg += "OK<br/>"
        msg += "Databases: %s<br/>" % ', '.join((str(x) for x in db_list))
        # Memory
        common_proxy = req.session.proxy('common')
        mem_usage = common_proxy.get_memory()
        msg += "<br/>Server mem usage: %s<br/>" % (mem_usage, )
        # Garbage collection
        get_count = common_proxy.gc_get_count()
        garbage = common_proxy.gc_garbage()
        msg += """<br/>Garbage infos: <br/>
        - get_count: %s<br/>
        - garbage: %s<br/>""" % (get_count, garbage)
    except Exception, e:
        msg += "KO<br/>Exception: %s" % _get_exception_message(e)
    finally:
        msg += '<br/>%s' % time.strftime('%Y-%m-%d %H:%M:%S %Z')
        return msg

WebClient.status = status
