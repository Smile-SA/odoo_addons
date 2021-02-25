# -*- coding: utf-8 -*-
# (C) 2020 Smile (<http://www.smile.fr>)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

import logging
import psutil
import shlex
from subprocess import PIPE, Popen
import time

from odoo import api, fields, models, SUPERUSER_ID
from odoo.modules.registry import Registry
from odoo.tools.func import wraps

from ..tools import s2human

_logger = logging.getLogger(__name__)

STATES = [
    ('running', 'Running'),
    ('done', 'Done'),
    ('killed', 'Killed'),
    ('failed', 'Failed'),
]


def state_cleaner(model):
    def decorator(method):
        @wraps(method)
        def wrapper(self, cr, *args, **kwargs):
            res = method(self, cr, *args, **kwargs)
            env = api.Environment(cr, SUPERUSER_ID, {})
            if model._name in env.registry.models:
                Model = env[model._name]
                cr.execute("select relname from pg_class "
                           "where relname='%s'" % model._table)
                if cr.rowcount:
                    Model.search(
                        [('state', '=', 'running')]).filtered(
                        lambda rec: not rec.pid or
                        not psutil.pid_exists(rec.pid)).kill()
            return res
        return wrapper
    return decorator


class TalendJobLogs(models.Model):
    _name = 'talend.job.logs'
    _description = 'Talend Job Logs'
    _rec_name = 'create_date'
    _order = 'create_date desc'

    def __init__(self, pool, cr):
        super(TalendJobLogs, self).__init__(pool, cr)
        model = pool[self._name]
        if not getattr(model, '_state_cleaner', False):
            model._state_cleaner = True
            setattr(Registry, 'setup_models', state_cleaner(model)(
                getattr(Registry, 'setup_models')))

    job_id = fields.Many2one(
        'talend.job', 'Talend Job', require=True, ondelete='cascade')
    state = fields.Selection(
        STATES, 'Status', readonly=True, required=True, default='running')
    pid = fields.Integer('Process Id', readonly=True)
    logs = fields.Text('Details', readonly=True, default="")
    create_date = fields.Datetime('Start Date', readonly=True)
    end_date = fields.Datetime(readonly=True)
    time = fields.Integer(compute='_get_time')
    time_human = fields.Char('Time', compute='_get_time')

    @api.depends('end_date')
    def _get_time(self):
        for record in self:
            to_date = record.end_date or fields.Datetime.now()
            timedelta = fields.Datetime.from_string(to_date) \
                - fields.Datetime.from_string(record.create_date)
            record.time = timedelta.total_seconds()
            record.time_human = s2human(record.time)

    @api.model
    def create(self, vals):
        log = super(TalendJobLogs, self).create(vals)
        log._run_job()
        return log

    def _run_job(self):
        for rec in self:
            try:
                rec.job_id._prepare()
                loop = rec.job_id.loop
                while loop:
                    rec._execute()
                    loop -= 1
            except Exception as e:
                rec.logs += str(e)
                rec.write({
                    'end_date': fields.Datetime.now(),
                    'state': 'failed',
                })
            else:
                rec.write({
                    'end_date': fields.Datetime.now(),
                    'state': 'done',
                })

    def _execute(self):
        for record in self:
            args = shlex.split(record.job_id.command)
            proc = Popen(args, stdout=PIPE, stderr=PIPE)
            record.pid = proc.pid
            while proc.poll() is None:
                # INFO: communicate returns (outs, errors)
                for index, logs in enumerate(proc.communicate()):
                    if logs:
                        logs = logs.decode('utf-8')
                        record.logs += '%s\n' % logs
                        if index:
                            _logger.error(logs)
                        else:
                            _logger.info(logs)
                time.sleep(1)

    def kill(self):
        self.filtered('pid')._kill()
        return self.write({'state': 'killed'})

    def _kill(self):
        for record in self:
            try:
                proc = psutil.Process(record.pid)
                proc.kill()
            except psutil.NoSuchProcess:
                pass

    def unlink(self):
        self.filtered(lambda talend_log: talend_log.state == 'running').kill()
        return super(TalendJobLogs, self).unlink()
