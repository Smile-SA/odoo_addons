# -*- coding: utf-8 -*-

import logging

from odoo import api, fields, models

_logger = logging.getLogger(__name__)


class Repository(models.Model):
    _inherit = 'scm.repository'

    id = fields.Integer(readonly=True)
    auto_create_branches = fields.Boolean(
        help="Define a default branch template to auto-create branches")
    default_branch_tmpl_id = fields.Many2one(
        'scm.repository.branch', 'Default branch template')
    auto_use_new_branch_in_ci = fields.Boolean()
    auto_delete_unactive_branches = fields.Boolean()

    @api.model
    def create(self, vals):
        return super(Repository, self.with_context(
            mail_create_nosubscribe=True)).create(vals)

    @api.multi
    @api.returns('scm.repository.branch', lambda records: records.ids)
    def create_branches(self):
        new_branches = self.env['scm.repository.branch'].browse()
        for repository in self.with_context(active_test=False):
            if not repository.vcs_id.cmd_list:
                continue
            default = {
                'branch_tmpl_id': repository.default_branch_tmpl_id.id,
                'use_in_ci': repository.auto_use_new_branch_in_ci,
            }
            try:
                branches = repository.list_branches()
            except Exception as e:
                _logger.error(e)
                continue
            branches_in_ci = repository.branch_ids.mapped('branch')
            for branch in branches:
                if branch not in branches_in_ci:
                    default['branch'] = branch
                    try:
                        new_branches |= repository.default_branch_tmpl_id.copy(
                            default)
                    except Exception as e:
                        _logger.error(e)
                        continue
        return new_branches

    @api.model
    @api.returns('scm.repository.branch', lambda records: records.ids)
    def auto_create_branch(self):
        repositories = self.search([('auto_create_branches', '=', True)])
        return repositories.create_branches()

    @api.multi
    def check_branches(self):
        super(Repository, self).check_branches()
        repositories = self.filtered(
            lambda repo: repo.auto_delete_unactive_branches)
        return self.env['scm.repository.branch'].search([
            ('repository_id', 'in', repositories.ids),
            ('active', '=', False),
        ]).unlink()
