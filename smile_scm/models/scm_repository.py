# -*- coding: utf-8 -*-

import logging
import os.path

from odoo import api, fields, models, _
from odoo.exceptions import UserError

from odoo.addons.smile_docker.tools import get_exception_message

_logger = logging.getLogger(__name__)


class Repository(models.Model):
    _name = 'scm.repository'
    _description = 'Repository'
    _inherit = ['mail.thread']
    _order = 'name'

    name = fields.Char(required=True)
    vcs_id = fields.Many2one('scm.vcs', 'Version Control System',
                             required=True, ondelete='restrict')
    url = fields.Char(required=True)
    partner_id = fields.Many2one('res.partner', 'Owner')
    tag_ids = fields.Many2many('scm.repository.tag', string="Tags")
    branch_ids = fields.One2many(
        'scm.repository.branch', 'repository_id', 'Branches')
    has_branch_done = fields.Boolean('Has at least a branch done',
                                     compute='_has_branch_done')
    branches_count = fields.Integer(
        'Branches Count', compute='_get_branches_count')
    can_switch_url = fields.Boolean(compute='_can_switch_url')
    new_url = fields.Char(compute='_get_url', inverse='_set_url')

    _sql_constraints = [
        ('unique_url', 'UNIQUE(url)', 'Repository URL must be unique'),
    ]

    @api.one
    @api.depends('branch_ids.state')
    def _has_branch_done(self):
        self.has_branch_done = self.branch_ids.filtered(
            lambda branch: branch.state == 'done')

    @api.one
    @api.depends('branch_ids')
    def _get_branches_count(self):
        self.branches_count = len(self.branch_ids)

    @api.one
    @api.depends('vcs_id')
    def _can_switch_url(self):
        self.can_switch_url = bool(self.vcs_id.cmd_switch_url)

    @api.one
    @api.depends('url')
    def _get_url(self):
        self.new_url = self.url

    @api.one
    def _set_url(self):
        for branch in self.branch_ids:
            if not os.path.isdir(branch.directory):
                continue
            self.vcs_id.switch_url(branch.directory, self.new_url)
        self.url = self.new_url

    @api.multi
    def copy_data(self, default=None):
        default = default or {}
        default['name'] = _('%s copy') % self.name
        return super(Repository, self).copy_data(default)

    @api.multi
    def list_branches(self):
        self.ensure_one()
        branches = self.branch_ids.filtered(
            lambda branch: branch.state == 'done')
        if not branches:
            raise UserError(
                _("You must define and clone a first branch for repository "
                  "%s before listing all of them") % self.name)
        branch = branches[-1]
        if not os.path.isdir(branch.directory):
            branch.clone(force=True)
        return self.vcs_id.list(branch.directory, self.url)

    @api.model
    def auto_check_branches(self):
        return self.search([]).check_branches()

    @api.multi
    def check_branches(self):
        branches_to_deactivate = self.env['scm.repository.branch'].browse()
        for repository in self:
            try:
                if not repository.vcs_id.cmd_list:
                    continue
                branches = repository.list_branches()
                for branch in repository.branch_ids:
                    if branch.branch not in branches:
                        branches_to_deactivate |= branch
            except Exception as e:
                msg = "Check branches failed"
                error = get_exception_message(e)
                _logger.error(msg + ' for repository %s\n\n%s' %
                              (repository.name, error))
                repository.message_post('\n\n'.join([_(msg), error]))
        return branches_to_deactivate.write({'active': False})

    @api.multi
    def open_switch_url_popup(self):
        self.ensure_one()
        return {
            'name': _('Switch URL'),
            'type': 'ir.actions.act_window',
            'res_model': self._name,
            'view_type': 'form',
            'view_mode': 'form',
            'view_id': self.env.ref('smile_scm.view_repository_swith_url_popup').id,
            'res_id': self.id,
            'target': 'new',
        }

    @api.multi
    def close_popup(self):
        return {'type': 'ir.actions.act_window_close'}
