# -*- encoding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2013 Smile (<http://www.smile.fr>). All Rights Reserved
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
import os
import re
import psycopg2
import shutil
from subprocess import call
import tempfile

from openerp import api, fields, models, _
from openerp.exceptions import Warning
from openerp.tools import config

from ..tools import cd

_logger = logging.getLogger(__package__)


class VersionControlSystem(models.Model):
    _name = 'scm.vcs'
    _description = 'Version Control System'

    name = fields.Char(required=True)
    cmd = fields.Char('Command', size=3, required=True)
    cmd_clone = fields.Char('Clone', required=True)
    cmd_pull = fields.Char('Pull', required=True)
    default_branch = fields.Char('Default branch')

    _sql_constraints = [
        ('unique_cmd', 'UNIQUE(cmd)', 'VCS must be unique'),
    ]


class OdooVersion(models.Model):
    _name = 'scm.version'
    _description = 'Odoo Version'
    _order = 'name'

    name = fields.Char(required=True)

    _sql_constraints = [
        ('unique_name', 'UNIQUE(name)', 'Odoo version must be unique'),
    ]


class Tag(models.Model):
    _name = 'scm.repository.tag'
    _description = 'Repository Tag'
    _order = 'name'

    name = fields.Char(required=True, translate=True)

    _sql_constraints = [
        ('unique_name', 'UNIQUE(name)', 'Repository tag must be unique'),
    ]


class Repository(models.Model):
    _name = 'scm.repository'
    _description = 'Repository'
    _inherit = ['mail.thread']

    @api.one
    def _has_branch_done(self):
        self.has_branch_done = self.branch_ids.filtered(lambda branch: branch.state == 'done')

    name = fields.Char(required=True)
    vcs_id = fields.Many2one('scm.vcs', 'Version Control System',
                             required=True, ondelete='restrict')
    url = fields.Char(size=256, required=True)
    partner_id = fields.Many2one('res.partner', 'Owner')
    tag_ids = fields.Many2many('scm.repository.tag', string="Tags")
    branch_ids = fields.One2many('scm.repository.branch', 'repository_id', 'Branches')
    has_branch_done = fields.Boolean('Has at least a branch done',
                                     compute='_has_branch_done', store=False)

    _sql_constraints = [
        ('unique_url', 'UNIQUE(url)', 'Repository URL must be unique'),
    ]


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
                                    readonly=True, states={'draft': [('readonly', False)]})
    branch = fields.Char(help="Technical branch name", required=True, readonly=True, states={'draft': [('readonly', False)]})
    version_id = fields.Many2one('scm.version', 'Odoo Version', required=True, ondelete="restrict",
                                 readonly=True, states={'draft': [('readonly', False)]})
    state = fields.Selection([
        ('draft', 'Not cloned'),
        ('done', 'Cloned'),
    ], required=True, readonly=True, default='draft', copyable=False)
    last_update = fields.Datetime(readonly=True, copyable=False)
    directory = fields.Char(compute='_get_directory')
    active = fields.Boolean(default=True)

    _sql_constraints = [
        ('unique_branch', 'UNIQUE(repository_id, branch)', 'Repository branch must be unique'),
    ]

    @api.multi
    def name_get(self):
        res = {}
        for branch in self:
            res[branch.id] = branch.name
            if branch.branch:
                res[branch.id] += ' %s' % branch.branch
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
                if not force and branch.state != 'draft':
                    raise Warning(_('You cannot clone a branch already cloned'))
                vcs = branch.vcs_id
                localdict = {'branch': branch.branch or branch.vcs_id.default_branch,
                             'url': branch.url}
                cmd_clone = vcs.cmd_clone % localdict
                cmd = cmd_clone.split(' ')
                cmd.insert(0, vcs.cmd)
                cmd.append(branch.directory)
                Branch._call(cmd)
        self.write({'state': 'done', 'last_update': fields.Datetime.now()})
        self.message_post(body=_("Branch cloned"))
        return True

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
                    Branch._call([vcs.cmd, vcs.cmd_pull])
                branch.write({'last_update': fields.Datetime.now()})
        return True

    @api.multi
    def unlink(self):
        for branch in self:
            try:
                shutil.rmtree(branch.directory)
            except:
                pass
        return super(Branch, self).unlink()
