# -*- coding: utf-8 -*-

import base64
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
    sequence = fields.Integer('Priority', required=True, default=15)
    archive_file = fields.Binary()
    context_file = fields.Binary()
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
    @api.depends('archive_file', 'child_ids.archive_file')
    def _get_job_version(self):
        if self.archive_file:
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
    @api.depends('name', 'path', 'args', 'context_file')
    def _get_command(self):
        cmd = [self._get_exefile()]
        if self.args:
            cmd += self.args.split(' ')
        if self.context_file:
            cmd += [
                '--context_param',
                'contextfile=%s' % self._get_contextfile(),
            ]
        self.command = ' '.join(cmd)

    @api.multi
    def run(self):
        jobs = self
        while jobs.mapped('child_ids'):
            self |= jobs.mapped('child_ids')
            jobs = jobs.mapped('child_ids')
        self.run_only()

    @api.multi
    def run_only(self):
        if self.mapped('log_ids').filtered(lambda log: log.state == 'running'):
            raise UserError(_('Execution already in progress'))
        if self._context.get('in_new_thread', True):
            thread = threading.Thread(
                target=self.filtered('archive_file')._run)
            thread.start()
        else:
            self.filtered('archive_file')._run()
        return True

    @api.one
    def _run(self):
        with api.Environment.manage():
            with registry(self._cr.dbname).cursor() as auto_cr:
                # autocommit: each insert/update request
                # will be performed automically. Thus
                # everyone (with another cursor) can access to
                # a running Talend job logs
                self = self.with_env(self.env(cr=auto_cr))
                self._cr.autocommit(True)
                self.log_ids.create({'job_id': self.id})

    @api.multi
    def _get_zipfile(self):
        self.ensure_one()
        bin_data = base64.b64decode(self.archive_file)
        f = io.BytesIO(bin_data)
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
        if self.context_file:
            context_file = self._get_contextfile()
            with open(context_file, 'wb') as cf:
                cf.write(base64.b64decode(self.context_file))

    @api.multi
    def refresh_logs(self):
        return True

    @api.multi
    def propagate_context(self):
        for job in self:
            children = job._get_all_children()
            children.write({'context_file': job.context_file})
        return True
