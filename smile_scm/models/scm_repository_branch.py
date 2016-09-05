# -*- coding: utf-8 -*-

import logging
import os
import re
import psycopg2
import shutil
from subprocess import call
import tempfile

from odoo import api, fields, models, _
from odoo.exceptions import Warning
from odoo.tools import config

from ..tools import cd

_logger = logging.getLogger(__package__)


class Branch(models.Model):
    _name = 'scm.repository.branch'
    _description = 'Branch'
    _inherit = ['mail.thread']
    _inherits = {'scm.repository': 'repository_id'}

    @api.one
    @api.depends('repository_id', 'repository_id.url', 'branch',
                 'repository_id.vcs_id', 'repository_id.vcs_id.cmd')
    def _get_directory(self):
        match = re.compile('([/@.])')
        if self.repository_id.url:
            directory = '%s_%s' % (self.vcs_id.cmd, match.sub('_', self.repository_id.url.split(':')[-1]))
            if self.branch:
                branch_name = self.branch
                for char in ': /':
                    branch_name = branch_name.replace(char, '_')
                directory += '_%s' % branch_name
            self.directory = os.path.join(self._parent_path, directory)

    repository_id = fields.Many2one('scm.repository', 'Repository', required=True, ondelete='cascade',
                                    readonly=True, states={'draft': [('readonly', False)]}, copy=False)
    branch = fields.Char(help="Technical branch name", readonly=True, states={'draft': [('readonly', False)]}, copy=False)
    version_id = fields.Many2one('scm.version', 'Odoo Version', required=True, ondelete="restrict",
                                 readonly=True, states={'draft': [('readonly', False)]})
    state = fields.Selection([
        ('draft', 'Not cloned'),
        ('done', 'Cloned'),
    ], required=True, readonly=True, default='draft', copy=False)
    last_update = fields.Datetime(readonly=True, copy=False)
    directory = fields.Char(compute='_get_directory', copy=False)
    active = fields.Boolean(default=True, copy=False)

    _sql_constraints = [
        ('unique_branch', 'UNIQUE(repository_id, branch)', 'Repository branch must be unique'),
    ]

    @api.multi
    def copy_data(self, default=None):
        data = super(Branch, self).copy_data(default)
        data.update(repository_id=self.repository_id.id)
        return data

    @api.multi
    def name_get(self):
        res = {}
        for branch in self:
            res[branch.id] = branch.name
            if branch.branch:
                res[branch.id] += ' (%s)' % branch.branch
        return res.items()

    @property
    def _parent_path(self):
        parent_path = config.get('repositories_path') or tempfile.gettempdir()
        if not os.path.isdir(parent_path):
            raise Warning(_("%s doesn't exist or is not a directory") % parent_path)
        return parent_path

    @staticmethod
    def _call(cmd):
        command = ' '.join(cmd)
        res = call(cmd)
        if res:
            _logger.debug("subprocess.call failed : %s" % res)
            raise Warning(_('%s FAILED' % command))
        _logger.info('%s SUCCEEDED' % command)

    @api.multi
    def _try_lock(self, warning=None):
        try:
            self._cr.execute("""SELECT id FROM "%s" WHERE id IN %%s FOR UPDATE NOWAIT""" % self._table,
                             (tuple(self.ids),), log_exceptions=False)
        except psycopg2.OperationalError:
            self._cr.rollback()  # INFO: Early rollback to allow translations to work for the user feedback
            if warning:
                raise Warning(warning)
            raise

    @api.multi
    def clone(self, force=False):
        self._try_lock(_('Cloning already in progress'))
        with cd(self._parent_path):
            for branch in self:
                if not branch.branch:
                    raise Warning(_('Please define a branch before cloning'))
                if not force and branch.state != 'draft':
                    raise Warning(_('You cannot clone a branch already cloned'))
                if os.path.exists(branch.directory):
                    branch.state = 'done'
                    branch.pull()
                else:
                    vcs = branch.vcs_id
                    localdict = {'branch': branch.branch or branch.vcs_id.default_branch,
                                 'url': branch.url}
                    cmd_clone = vcs.cmd_clone % localdict
                    cmd = cmd_clone.split(' ')
                    cmd.insert(0, vcs.cmd)
                    cmd.append(branch.directory)
                    try:
                        Branch._call(cmd)
                    except Warning:
                        _logger.error('Clone failed for branch %s (%s %s)...' % (branch.id, branch.name, branch.branch))
                        raise
                    else:
                        branch.message_post(body=_("Branch cloned"))
        return self.write({'state': 'done', 'last_update': fields.Datetime.now()})

    @api.multi
    def pull(self):
        for branch in self:
            if branch.state == 'draft':
                raise Warning(_('You cannot pull a repository not cloned'))
            if not os.path.exists(branch.directory):
                branch.clone(force=True)
            else:
                with cd(branch.directory):
                    vcs = branch.vcs_id
                    try:
                        Branch._call([vcs.cmd, vcs.cmd_pull])
                    except Warning:
                        _logger.error('Pull failed for branch %s (%s %s)...' % (branch.id, branch.name, branch.branch))
                        raise
                branch.write({'last_update': fields.Datetime.now()})
        return True

    def _clean_branch(self, vals):
        "Remove spaces from branch"
        if not vals.get('branch'):
            return
        vals['branch'] = "".join(vals['branch'].split())

    @api.model
    def create(self, vals):
        self._clean_branch(vals)
        return super(Branch, self).create(vals)

    @api.multi
    def write(self, vals):
        self._clean_branch(vals)
        return super(Branch, self).write(vals)

    @api.multi
    def unlink(self):
        for branch in self:
            try:
                shutil.rmtree(branch.directory)
            except:
                pass
        return super(Branch, self).unlink()
