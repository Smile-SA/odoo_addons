# -*- coding: utf-8 -*-

import base64
import logging
import io
import os
import psycopg2
import stat
from subprocess import PIPE, Popen
import sys
import tempfile
import threading
import time
import zipfile

from odoo import api, fields, models, registry, _
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)


class TalendJob(models.Model):
    _name = 'talend.job'
    _description = 'Talend Job'

    name = fields.Char(required=True)
    archive_file = fields.Binary(required=True)
    context_file = fields.Binary()
    path = fields.Char()
    args = fields.Char()
    log_ids = fields.One2many(
        'talend.job.logs', 'job_id', 'Logs', readonly=True)

    @api.multi
    def run(self):
        thread = threading.Thread(target=self._run)
        thread.start()
        return True

    @api.one
    def _run(self):
        with api.Environment.manage():
            with registry(self._cr.dbname).cursor() as new_cr:
                self.with_env(self.env(cr=new_cr))._try_lock()
                with registry(self._cr.dbname).cursor() as auto_cr:
                    # autocommit: each insert/update request
                    # will be performed automically. Thus
                    # everyone (with another cursor) can access to
                    # a running Talend job logs
                    self = self.with_env(self.env(cr=auto_cr))
                    self._cr.autocommit(True)
                    self._prepare()
                    self._execute()

    @api.multi
    def _try_lock(self):
        try:
            self._cr.execute(
                """SELECT id FROM "%s" WHERE id IN %%s FOR UPDATE NOWAIT"""
                % self._table, (tuple(self.ids),), log_exceptions=False)
        except psycopg2.OperationalError:
            # INFO: Early rollback to allow translations to work
            # for the user feedback
            self._cr.rollback()
            raise UserError(_('Execution already in progress'))

    @api.multi
    def _get_path(self):
        self.ensure_one()
        return self.path or tempfile.gettempdir()

    @api.multi
    def _get_exefile(self):
        ext = 'bat' if sys.platform == 'win32' else 'sh'
        return os.path.join(
            self._get_path(), self.name, '%s_run.%s' % (self.name, ext))

    @api.multi
    def _get_contextfile(self):
        return os.path.join(
            self._get_path(), 'defaults.properties')

    @api.one
    def _prepare(self):
        bin_data = base64.b64decode(self.archive_file)
        f = io.BytesIO(bin_data)
        if not zipfile.is_zipfile(f):
            raise UserError(_('This module support only zipfiles'))
        zf = zipfile.ZipFile(f, mode='w')
        zf.extractall(self._get_path())
        if not os.path.exists(self._get_exefile()):
            zf = zipfile.ZipFile(f)
            zf.extractall(self._get_path())
        os.chmod(self._get_exefile(), stat.S_IRUSR + stat.S_IXUSR)
        if self.context_file:
            context_file = self._get_contextfile()
            with open(context_file, 'wb') as cf:
                cf.write(base64.b64decode(self.context_file))

    @api.one
    def _execute(self):
        cmd = [self._get_exefile()]
        if self.args:
            cmd += self.args.split(' ')
        if self.context_file:
            cmd += [
                '--context_param',
                'contextfile=%s' % self._get_contextfile(),
            ]
        log = self.log_ids.create({'job_id': self.id})
        proc = Popen(cmd, stdout=PIPE, stderr=PIPE)
        while proc.poll() is None:
            # INFO: communicate returns (outs, errors)
            for index, logs in enumerate(proc.communicate()):
                if logs:
                    logs = logs.decode('utf-8')
                    log.logs += '%s\n' % logs
                    if index:
                        _logger.error(logs)
                    else:
                        _logger.info(logs)
            time.sleep(1)
        log.end_date = fields.Datetime.now()

    @api.multi
    def refresh_logs(self):
        return True


class TalendJobLogs(models.Model):
    _name = 'talend.job.logs'
    _description = 'Talend Job Logs'
    _rec_name = 'logs'
    _order = 'create_date desc'

    job_id = fields.Many2one(
        'talend.job', 'Talend Job', require=True, ondelete='cascade')
    logs = fields.Text(readonly=True, default="")
    create_date = fields.Datetime('Start Date', readonly=True)
    end_date = fields.Datetime(readonly=True)
