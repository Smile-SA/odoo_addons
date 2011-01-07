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

import logging
import logging.handlers
import threading
import pooler
import tools
from re import escape

class SmileDBHandler(logging.Handler):
    def emit(self, record):
        levelno = getattr(logging, tools.config['log2db'].upper())
        if record.levelno <= levelno or (logging.TEST >= levelno and record.levelno == logging.WARNING and record.name.startswith('tests.')):
            dbname = getattr(threading.currentThread(), 'dbname', '')
            if dbname:
                db, pool = pooler.get_db_and_pool(dbname, update_module=tools.config['init'] or tools.config['update'], pooljobs=False)
                cr = db.cursor()
                log_table = 'syslog'

                if logging.TEST >= levelno and record.levelno == logging.WARNING and record.name.startswith('tests.'):
                    cr.execute("SELECT max(id) FROM %s" % (log_table,))
                    id = cr.fetchone()
                    params = (log_table, record.msg, id[0])
                    query = "UPDATE %s SET (failed, exception) = (TRUE, '%s') WHERE id = %d"

                else:
                    cr.execute("SELECT relname FROM pg_class WHERE relname = '%s'" % (log_table,))
                    if not cr.rowcount:
                        cr.execute("""CREATE TABLE %s (
id serial NOT NULL,
create_uid integer,
create_date timestamp without time zone,
write_date timestamp without time zone,
write_uid integer,
name character varying(128),
levelno integer,
levelname character varying(64),
lineno integer,
module character varying(128),
msecs numeric,
pathname character varying(255),
message text,
failed boolean,
exception text
)""" % (log_table,))

                    params = (log_table, record.name, record.levelno, record.levelname, record.lineno, record.module, record.msecs, record.pathname, escape(record.msg),)
                    query = """INSERT INTO %s (
create_uid,
create_date,
name,
levelno,
levelname,
lineno,
module,
msecs,
pathname,
message)
VALUES (1, now(), '%s', %d, '%s', %d, '%s', %.f, '%s', '%s')"""

                try:
                    cr.execute(query % params)
                    cr.commit()
                except Exception, e:
                    record.msg = tools.ustr(e) + "\n" + record.msg
                finally:
                    cr.close()
        return True
