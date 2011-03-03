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

from datetime import datetime
import time

import netsvc
from osv import fields, osv
import pooler
import tools

from base.ir.ir_cron import str2tuple, _intervalTypes

class ir_cron(osv.osv, netsvc.Agent):
    _inherit = "ir.cron"

    _columns = {
        'report': fields.text('Last Execution Report'),
    }

    def _callback(self, cr, uid, model, func, args):
        args = str2tuple(args)
        m = self.pool.get(model)
        try:
            f = getattr(m, func)
            f(cr, uid, *args)
        except:
            cr.rollback()
            self._logger.exception("Job call of self.pool.get('%s').%s(cr, uid, *%r) failed" % (model, func, args))
            raise

    def _poolJobs(self, db_name, check=False):
        # Added by Smile
        report = """Here is the action scheduling report.

        Start Time: %s
        End Time: %s

        """
        ##
        try:
            db, pool = pooler.get_db_and_pool(db_name)
        except:
            return False
        cr = db.cursor()
        try:
            if not pool._init:
                now = datetime.now()
                cr.execute('select * from ir_cron where numbercall<>0 and active and nextcall<=now() order by priority')
                for job in cr.dictfetchall():
                    # Added by Smile
                    start_time = time.strftime('%Y-%m-%d %H:%M:%S')
                    try:
                    ##
                        nextcall = datetime.strptime(job['nextcall'], '%Y-%m-%d %H:%M:%S')
                        numbercall = job['numbercall']
    
                        ok = False
                        while nextcall < now and numbercall:
                            if numbercall > 0:
                                numbercall -= 1
                            if not ok or job['doall']:
                                self._callback(cr, job['user_id'], job['model'], job['function'], job['args'])
                            if numbercall:
                                nextcall += _intervalTypes[job['interval_type']](job['interval_number'])
                            ok = True
                        addsql = ''
                        if not numbercall:
                            addsql = ', active=False'
                        cr.execute("update ir_cron set nextcall=%s, numbercall=%s" + addsql + " where id=%s", (nextcall.strftime('%Y-%m-%d %H:%M:%S'), numbercall, job['id']))
                    # Added by Smile
                        report += "No exceptions"
                    except Exception, e:
                        report += "Exception:\n" + tools.ustr(e)
                    end_time = time.strftime('%Y-%m-%d %H:%M:%S')
                    self.write(cr, 1, job['id'], {'report': report % (start_time, end_time)})
                    ##
                    cr.commit()

            cr.execute('select min(nextcall) as min_next_call from ir_cron where numbercall<>0 and active')
            next_call = cr.dictfetchone()['min_next_call']
            if next_call:
                next_call = time.mktime(time.strptime(next_call, '%Y-%m-%d %H:%M:%S'))
            else:
                next_call = int(time.time()) + 3600   # if do not find active cron job from database, it will run again after 1 day

            if not check:
                self.setAlarm(self._poolJobs, next_call, db_name, db_name)

        except Exception, ex:            
            self._logger.warning('Exception in cron:', exc_info=True)

        finally:
            cr.commit()
            cr.close()

ir_cron()
