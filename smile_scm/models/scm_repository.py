# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.exceptions import UserError


class Repository(models.Model):
    _name = 'scm.repository'
    _description = 'Repository'
    _inherit = ['mail.thread']
    _order = 'name'

    @api.one
    @api.depends('branch_ids.state')
    def _has_branch_done(self):
        self.has_branch_done = self.branch_ids.filtered(lambda branch: branch.state == 'done')

    @api.one
    @api.depends('branch_ids')
    def _get_branches_count(self):
        self.branches_count = len(self.branch_ids)

    name = fields.Char(required=True)
    vcs_id = fields.Many2one('scm.vcs', 'Version Control System',
                             required=True, ondelete='restrict')
    url = fields.Char(size=256, required=True)
    partner_id = fields.Many2one('res.partner', 'Owner')
    tag_ids = fields.Many2many('scm.repository.tag', string="Tags")
    branch_ids = fields.One2many('scm.repository.branch', 'repository_id', 'Branches')
    has_branch_done = fields.Boolean('Has at least a branch done',
                                     compute='_has_branch_done', store=False)
    branches_count = fields.Integer('Branches Count', compute='_get_branches_count', store=False)

    _sql_constraints = [
        ('unique_url', 'UNIQUE(url)', 'Repository URL must be unique'),
    ]

    @api.multi
    def copy_data(self, default=None):
        default = default or {}
        default['name'] = _('%s copy') % self.name
        return super(Repository, self).copy_data(default)

    @api.multi
    def list_branches(self):
        self.ensure_one()
        if not self.branch_ids:
            raise UserError(_("You must define a first branch for repository %s before listing all of them") % self.name)
        return self.vcs_id.list(self.branch_ids[0].directory, self.url)

    @api.multi
    def check_branches(self):
        if not self.ids:
            self = self.search([])
        branches_to_deactivate = self.env['scm.repository.branch'].browse()
        for repository in self:
            if not repository.vcs_id.cmd_list:
                continue
            branches = repository.list_branches()
            for branch in repository.branch_ids:
                if branch.branch not in branches:
                    branches_to_deactivate |= branch
        return branches_to_deactivate.write({'active': False})
