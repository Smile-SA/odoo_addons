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

import datetime
import logging
import threading

import pooler
import tools

class SartreDBHandler(logging.Handler):

    def __init__(self, level=logging.NOTSET):
        logging.Handler.__init__(self, level)
        self._dbname_to_cr = {}

    def emit(self, record):
        dbname = getattr(threading.currentThread(), 'dbname', '')
        db, pool = pooler.get_db_and_pool(dbname, update_module=tools.config['init'] or tools.config['update'], pooljobs=False)
        cr = self._dbname_to_cr.get(dbname, False)
        if not cr:
            cr = self._dbname_to_cr[dbname] = db.cursor()
        trigger_id = record.args and isinstance(record.args, dict) and record.args.get('trigger_id', False) or False
        uid = record.args and isinstance(record.args, dict) and record.args.get('uid', False) or False
        
        if uid and pool.get('res.users').exists(cr, 1, uid):
            sartre_log_obj = pool.get('sartre.log')
            sartre_log_obj.create(cr, uid, {
                'trigger_id': trigger_id,
                'level': record.levelname,
                'message': record.msg,
            })
        else:
            cr.execute("INSERT INTO sartre_log (create_date, trigger_id, level, message) VALUES (now(), %s, %s, %s)",
                       (trigger_id,
                        record.levelname,
                        record.msg,))
        cr.commit()
        return True

    def close(self):
        logging.Handler.close(self)
        for cr in self._dbname_to_cr.values():
            cr.close()
        self._dbname_to_cr = {}

logger = logging.getLogger("smile_action_trigger")
handler = SartreDBHandler()
logger.addHandler(handler)

class SartreLogger():
    
    def __init__(self, uid, trigger_id):
        assert isinstance(uid, (int, long)), 'uid should be an integer'
        self.logger = logging.getLogger("smile_action_trigger")
        self.uid = uid
        self.trigger_id = trigger_id
        self.trigger_start = datetime.datetime.now()
        self.logger_args = {'trigger_id': trigger_id, 'uid': uid}

    def info(self, msg):
        self.logger.info(msg, self.logger_args)

    def warning(self, msg):
        self.logger.warning(msg, self.logger_args)
        
    def error(self, msg):
        self.logger.error(msg, self.logger_args)
        
    def critical(self, msg):
        self.logger.critical(msg, self.logger_args)
        
    def log(self, msg):
        self.logger.log(msg, self.logger_args)

    def exception(self, msg):
        self.logger.exception(msg, self.logger_args)
        
    def time_info(self, msg):
        delay = datetime.datetime.now() - self.trigger_start
        msg += " after %sh %smin %ss" % tuple(str(delay).split(':'))
        self.logger.info(msg, self.logger_args)
