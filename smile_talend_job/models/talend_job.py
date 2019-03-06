# -*- coding: utf-8 -*-
# (C) 2018 Smile (<http://www.smile.fr>)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

import base64
import binascii
import codecs
import csv
import io
import os
import stat
import sys
import tempfile
import threading
import zipfile

from odoo import api, fields, models, registry, _
from odoo.exceptions import UserError, ValidationError

from .talend_job_logs import STATES


class TalendJob(models.Model):
    _name = 'talend.job'
    _description = 'Talend Job'
    _inherit = 'mail.thread'
    _order = 'sequence, id'

    name = fields.Char(required=True)
    active = fields.Boolean(default=True)
    sequence = fields.Integer('Priority', required=True, default=15)
    archive = fields.Binary()
    context = fields.Text()
    path = fields.Char()
    args = fields.Char()
    log_ids = fields.One2many(
        'talend.job.logs', 'job_id', 'Logs', readonly=True, copy=False)
    parent_id = fields.Many2one('talend.job', 'Parent')
    child_ids = fields.One2many(
        'talend.job', 'parent_id', 'Children', copy=False)
    version = fields.Char(
        compute='_get_job_version', store=True)
    command = fields.Char(compute='_get_command')
    loop = fields.Integer(required=True, default=1)
    last_log_date = fields.Datetime(
        'Last Execution Date', compute='_get_last_log_infos')
    last_log_state = fields.Selection(
        STATES, 'Last Execution Status', compute='_get_last_log_infos')

    @api.constrains('parent_id')
    def _check_hierarchy(self):
        if not self._check_recursion():
            raise ValidationError(_('Error! You cannot create '
                                    'recursive hierarchy of Talend jobs.'))

    @api.one
    @api.depends('archive', 'child_ids.archive')
    def _get_job_version(self):
        if self.archive:
            with self._get_zipfile() as zf:
                filename = 'jobInfo.properties'
                # INFO: can't use configparser because this file has no section
                with zf.open(filename) as f:
                    reader = csv.reader(
                        codecs.iterdecode(f.readlines(), 'utf-8'),
                        delimiter='=', escapechar='\\', quoting=csv.QUOTE_NONE)
                    for row in reader:
                        if row[0] == 'jobVersion':
                            self.version = row[1]
        else:
            self.version = max(
                self._get_all_children().filtered('version').mapped('version'),
                default='')

    @api.multi
    def _get_all_children(self):
        all_children = children = self.mapped('child_ids')
        while children.mapped('child_ids'):
            children = children.mapped('child_ids')
            all_children |= children
        return all_children

    @api.one
    @api.depends('log_ids.state')
    def _get_last_log_infos(self):
        not_killed_logs = self.log_ids.filtered(
            lambda log: log.state != 'killed')
        if not_killed_logs:
            last_log = not_killed_logs.sorted('create_date')[-1]
            self.last_log_date = last_log.create_date
            self.last_log_state = last_log.state
        else:
            self.last_log_date = False
            self.last_log_state = False

    @api.one
    @api.depends('name', 'path', 'args', 'context')
    def _get_command(self):
        cmd = [self._get_exefile()]
        if self.args:
            cmd += self.args.split(' ')
        context = self.context and \
            self.context.replace(' ', '').replace('\t', '') or ''
        for param in filter(bool, context.split('\n')):
            cmd += ['--context_param', param]
        self.command = ' '.join(cmd)

    @api.multi
    def run(self):
        return self._run()

    @api.multi
    def run_only(self):
        return self._run(depth=1)

    @api.multi
    def _run(self, depth=-1):
        queue = []
        self._build_queue(queue, depth)
        if self._context.get('in_new_thread', True):
            thread = threading.Thread(
                target=self._process_queue, args=(queue,))
            thread.start()
        else:
            self._process_queue(queue)
        return True

    @api.multi
    def _build_queue(self, queue, depth=-1):
        if depth:
            depth -= 1
            self._check_execution()
            for job in self:
                if job.archive:
                    queue.append(job.id)
                job.child_ids._build_queue(queue, depth)

    @api.multi
    def _check_execution(self):
        if self.mapped('log_ids').filtered(lambda log: log.state == 'running'):
            raise UserError(_('Execution already in progress'))

    @api.model
    def _process_queue(self, queue):
        queue.reverse()
        while queue:
            job_id = queue.pop()
            self._process_job(job_id)

    @api.model
    def _process_job(self, job_id):
        with api.Environment.manage():
            with registry(self._cr.dbname).cursor() as auto_cr:
                # autocommit: each insert/update request
                # will be performed automically. Thus
                # everyone (with another cursor) can access to
                # a running Talend job logs
                self = self.with_env(self.env(cr=auto_cr))
                self._cr.autocommit(True)
                self.env['talend.job.logs'].create({'job_id': job_id})

    @api.multi
    def _get_zipfile(self):
        self.ensure_one()
        data = self.archive
        try:
            data = base64.b64decode(data)
        except binascii.Error:
            pass
        f = io.BytesIO(data)
        if not zipfile.is_zipfile(f):
            raise UserError(_('This module support only zipfiles'))
        return zipfile.ZipFile(f)

    @api.multi
    def _get_path(self):
        self.ensure_one()
        path = self.path or tempfile.gettempdir()
        if not os.path.exists(path):
            os.makedirs(path)
        return path

    @api.multi
    def _get_exefile(self):
        ext = 'bat' if sys.platform == 'win32' else 'sh'
        return os.path.join(
            self._get_path(), self.name, '%s_run.%s' % (self.name, ext))

    @api.multi
    def _get_contextfile(self):
        return os.path.join(self._get_path(), 'defaults.properties')

    @api.one
    def _prepare(self):
        with self._get_zipfile() as zf:
            zf.extractall(self._get_path())
        os.chmod(self._get_exefile(),
                 # -rwxr-xr-x
                 stat.S_IRWXU +
                 stat.S_IRGRP + stat.S_IXGRP +
                 stat.S_IROTH + stat.S_IXOTH)

    @api.multi
    def refresh_logs(self):
        return True

    @api.multi
    def propagate_context(self):
        for job in self:
            children = job.with_context(active_test=False)._get_all_children()
            children.write({'context': job.context})
        return True
