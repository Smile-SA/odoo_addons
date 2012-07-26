# -*- encoding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2011 Smile (<http://www.smile.fr>). All Rights Reserved
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

from openobject.errors import TinyError, TinyException
from openobject.tools import expose
from openerp.controllers import unsecured
from openerp.controllers.root import Root
from openerp.utils import rpc


def _get_exception_message(e):
    msg = e
    if isinstance(e, (TinyError, TinyException)):
        msg = e.message
    if msg == 'Connection refused':
        msg = 'Connection to the OpenERP server failed'
    elif 'psycopg2.connect' in msg:
        msg = 'Connection to the PostgreSQL server failed<br/>%s' % msg
    return msg


@expose()
@unsecured
def status(self):
    msg = "OpenERP Server: "
    try:
        db_list = rpc.session.execute_noauth('db', 'list', True)
        msg += "OK<br/>"
        msg += "Databases: %s<br/>" % ', '.join(map(str, db_list))
        # Memory
        mem_usage = rpc.session.execute_noauth('common', 'get_memory')
        msg += "<br/>Server mem usage: %s<br/>" % (mem_usage, )
        # Garbage collection
        get_count = rpc.session.execute_noauth('common', 'gc_get_count')
        garbage = rpc.session.execute_noauth('common', 'gc_garbage')
        msg += """<br/>Garbage infos: <br/>
        - get_count: %s<br/>
        - garbage: %s<br/>""" % (get_count, garbage)

    except Exception, e:
        msg += "KO<br/>Exception: %s" % _get_exception_message(e)
    finally:
        msg += '<br/>%s' % time.strftime('%Y-%m-%d %H:%M:%S %Z')
        return msg

Root.status = status
