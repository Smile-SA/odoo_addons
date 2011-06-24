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

import logging
from re import escape
import threading

import pooler
import tools

class SmileImportDBHandler(logging.Handler):

    def __init__(self, level=logging.NOTSET):
        logging.Handler.__init__(self, level)
        self._dbname_to_cr = {}
        
    def emit(self, record):
        dbname = getattr(threading.currentThread(), 'dbname', '')
        db, pool = pooler.get_db_and_pool(dbname, update_module=tools.config['init'] or tools.config['update'], pooljobs=False)
        cr = self._dbname_to_cr.get(dbname, False)
        if not cr:
            cr = self._dbname_to_cr[dbname] = db.cursor()
        import_id = record.args and isinstance(record.args, dict) and record.args.get('import_id', False) or False 
        import_log_obj = pool.get('ir.model.import.log')
        import_log_obj.create(cr, 1, {
            'import_id': import_id,
            'level': record.levelname,
            'message': escape(record.msg),
        })
        cr.commit()
        return True

    def close(self):
        logging.Handler.close(self)
        for cr in self._dbname_to_cr.values():
            cr.close()
        self._dbname_to_cr = {}

logger = logging.getLogger("smile_import")
handler = SmileImportDBHandler()
logger.addHandler(handler)
