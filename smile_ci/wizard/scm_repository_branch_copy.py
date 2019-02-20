# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


class ScmRepositoryBranchCopyWizard(models.TransientModel):
    _name = 'scm.repository.branch.copy'
    _description = 'Branch Duplicate Wizard'

    name = fields.Char('New branch', required=True)
    branch_id = fields.Many2one(
        'scm.repository.branch', 'Origin branch',
        required=True, invisible=True)

    @api.one
    @api.constrains('name')
    def _check_name(self):
        all_branches = self.branch_id.repository_id. \
            with_context(active_test=False).branch_ids.mapped('branch')
        if self.name in all_branches:
            raise ValidationError(
                _('The branch %s already exists (maybe archived)') % self.name)

    @api.multi
    def validate(self):
        self.ensure_one()
        new_branch = self.branch_id.copy({'branch': self.name})
        return new_branch.open_wizard()
