# -*- coding: utf-8 -*-

import logging
import os.path
import re
import psycopg2
import shutil
import tempfile

from odoo import api, fields, models, _
from odoo.exceptions import UserError
from odoo.tools import config

_logger = logging.getLogger(__name__)


class Branch(models.Model):
    _name = 'scm.repository.branch'
    _description = 'Branch'
    _inherit = ['mail.thread']
    _inherits = {'scm.repository': 'repository_id'}
    _order = 'branch'

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
    ], 'Status', required=True, readonly=True, default='draft', copy=False)
    last_update = fields.Datetime(readonly=True, copy=False)
    directory = fields.Char(compute='_get_directory', copy=False)
    active = fields.Boolean(default=True, copy=False)

    _sql_constraints = [
        ('unique_branch', 'UNIQUE(repository_id, branch)', 'Repository branch must be unique'),
    ]

    @api.multi
    def copy_data(self, default=None):
        data = super(Branch, self).copy_data(default)
        data[0].update(repository_id=self.repository_id.id)
        return data

    @api.multi
    def name_get(self):
        res = {}
        for branch in self:
            res[branch.id] = branch.name
            if branch.branch:
                res[branch.id] += ' (%s)' % branch.branch
        return res.items()

    @api.model
    def search(self, args, offset=0, limit=None, order=None, count=False):
        records = super(Branch, self).search(args, offset, limit, order, count)
        if not order and not count:
            return records.sorted(key='name')
        return records

    @property
    def _parent_path(self):
        parent_path = config.get('repositories_path') or tempfile.gettempdir()
        if not os.path.isdir(parent_path):
            raise UserError(_("%s doesn't exist or is not a directory") % parent_path)
        return parent_path

    @api.multi
    def _try_lock(self, warning=None):
        try:
            self._cr.execute("""SELECT id FROM "%s" WHERE id IN %%s FOR UPDATE NOWAIT""" % self._table,
                             (tuple(self.ids),), log_exceptions=False)
        except psycopg2.OperationalError:
            self._cr.rollback()  # INFO: Early rollback to allow translations to work for the user feedback
            if warning:
                raise UserError(warning)
            raise

    @api.multi
    def clone(self, force=False):
        self._try_lock(_('Cloning already in progress'))
        for branch in self:
            if not branch.branch:
                raise UserError(_('Please define a branch before cloning'))
            if not force and branch.state != 'draft':
                raise UserError(_('You cannot clone a branch already cloned'))
            branch_directory = os.path.join(self._parent_path, branch.directory)
            if os.path.exists(branch_directory):
                branch.state = 'done'
                branch.pull()
            else:
                try:
                    branch.vcs_id.clone(branch_directory, branch.branch, branch.url)
                except UserError:
                    _logger.error('Clone failed for branch %s (%s %s)...' % (branch.id, branch.name, branch.branch))
                    raise
                else:
                    branch.message_post(body=_("Branch cloned"))
        return self.write({'state': 'done', 'last_update': fields.Datetime.now()})

    @api.multi
    def pull(self):
        for branch in self:
            if branch.state == 'draft':
                raise UserError(_('You cannot pull a repository not cloned'))
            if not os.path.exists(branch.directory):
                branch.clone(force=True)
            else:
                try:
                    branch.vcs_id.pull(branch.directory)
                except UserError:
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
                if branch.directory and os.path.exists(branch.directory):
                    shutil.rmtree(branch.directory)
            except Exception, e:
                _logger.error('Remove branch directory failed\n%s' % repr(e))
                pass
        return super(Branch, self).unlink()

    @api.multi
    def open_repository(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': _('Repository'),
            'res_model': self.repository_id._name,
            'view_mode': 'form',
            'res_id': self.repository_id.id,
            'target': 'blank',
        }
