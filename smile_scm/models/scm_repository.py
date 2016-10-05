# -*- coding: utf-8 -*-

from odoo import api, fields, models, _


class Repository(models.Model):
    _name = 'scm.repository'
    _description = 'Repository'
    _inherit = ['mail.thread']
    _order = 'name'

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

    @api.multi
    def copy_data(self, default=None):
        default = default or {}
        default['name'] = _('%s copy') % self.name
        return super(Repository, self).copy_data(default)
