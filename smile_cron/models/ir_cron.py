# -*- coding: utf-8 -*-

import pytz

from datetime import datetime
from dateutil.relativedelta import relativedelta

from openerp import api, fields, models, SUPERUSER_ID
from openerp.tools import DEFAULT_SERVER_DATETIME_FORMAT
from openerp.osv import fields as osv_fields


_intervalTypes = {
    'work_days': lambda interval: relativedelta(days=interval),
    'days': lambda interval: relativedelta(days=interval),
    'hours': lambda interval: relativedelta(hours=interval),
    'weeks': lambda interval: relativedelta(days=7*interval),
    'months': lambda interval: relativedelta(months=interval),
    'minutes': lambda interval: relativedelta(minutes=interval),
}

class IrCron(models.Model):
    """
        Extend ir.cron to add functionality allowing for a list of distinct execution
        times for a cron job.
    """
    _inherit = 'ir.cron'

    schedule_type = fields.Selection([('default', 'Default'), ('timesheet', 'Timesheet')],
                                     'Cron schedule type', default='default')
    call_time_ids = fields.One2many('ir.cron.time', 'cron_job_id', 'Timesheet')

    @api.onchange('call_time_ids')
    def _onchange_call_time_ids(self):
        if self.call_time_ids:
            self.nextcall = self._next_call_time()
        else:
            self.nextcall = None

    @api.multi
    def _next_call_time(self):
        return min(self.call_time_ids.mapped('call_time'))

    def _process_job(self, job_cr, job, cron_cr):
        """
            Adapted from default ir.cron method to add processing of cron jobs
            based on a time sheet of execution times.
        """

        if job.get('schedule_type') == 'default':
            super(IrCron, self)._process_job(job_cr, job, cron_cr)
        else:
            try:
                with api.Environment.manage():
                    now = osv_fields.datetime.context_timestamp(job_cr, job['user_id'], datetime.now())
                    numbercall = job['numbercall']

                    call_time_ids = self.pool['ir.cron.time'].search(job_cr, job['user_id'],
                                                                     [('cron_job_id', '=', job['id'])])
                    call_times = self.pool['ir.cron.time'].browse(job_cr, job['user_id'], call_time_ids)
                    for call in call_times:
                        call_time = osv_fields.datetime.context_timestamp(job_cr, job['user_id'],
                                                                          datetime.strptime(call.call_time,
                                                                          DEFAULT_SERVER_DATETIME_FORMAT))
                        ok = False
                        while call_time < now and numbercall:
                            if not ok or job['doall']:
                                self._callback(job_cr, job['user_id'], job['model'], job['function'],
                                               job['args'], job['id'])
                                if numbercall > 0:
                                    numbercall -= 1
                            if numbercall:
                                call_time += _intervalTypes[job['interval_type']](job['interval_number'])
                                cron_cr.execute("UPDATE ir_cron_time SET call_time=%s WHERE id=%s",
                                                (call_time.astimezone(pytz.UTC).strftime(
                                                    DEFAULT_SERVER_DATETIME_FORMAT), call.id))
                            ok = True

                    addsql = ''
                    if not numbercall:
                        addsql = ', active=False'
                    cron_cr.execute("UPDATE ir_cron SET nextcall=(SELECT min(call_time) FROM ir_cron_time "
                                    "WHERE cron_job_id=%s), numbercall=%s"+addsql+" WHERE id=%s",
                                    (job['id'], numbercall, job['id']))
                    self.invalidate_cache(job_cr, SUPERUSER_ID)

            finally:
                job_cr.commit()
                cron_cr.commit()
