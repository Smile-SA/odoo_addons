# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


class Repository(models.Model):
    _inherit = 'scm.repository'

    id = fields.Integer(readonly=True)
    auto_create_branches = fields.Boolean(help="Define a default branch template to auto-create branches")
    default_branch_tmpl_id = fields.Many2one('scm.repository.branch', 'Default branch template')

    @api.one
    @api.constrains('auto_create_branches', 'default_branch_tmpl_id')
    def _check_default_branch_tmpl(self):
        if self.auto_create_branches and not self.default_branch_tmpl_id:
            raise ValidationError(_('Branches auto-creation requires to define a default branch template'))

    @api.model
    def create(self, vals):
        return super(Repository, self.with_context(mail_create_nosubscribe=True)).create(vals)

    @api.multi
    @api.returns('scm.repository.branch', lambda records: records.ids)
    def create_branches(self):
        if not self.ids:
            self = self.search([('auto_create_branches', '=', True)])
        new_branches = self.env['scm.repository.branch'].browse()
        for repository in self:
            if not repository.vcs_id.cmd_list:
                continue
            default = {'branch_tmpl_id': repository.default_branch_tmpl_id.id}
            branches = repository.list_branches()
            branches_in_ci = repository.branch_ids.mapped('branch')
            for branch in branches:
                if branch not in branches_in_ci:
                    default['branch'] = branch
                    new_branches |= repository.default_branch_tmpl_id.copy(default)
        return new_branches
