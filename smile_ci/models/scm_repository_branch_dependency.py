# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.exceptions import UserError


class BranchDependency(models.Model):
    _name = 'scm.repository.branch.dependency'
    _description = 'Merge with branch'
    _rec_name = 'branch_id'

    branch_id = fields.Many2one('scm.repository.branch', 'Branch', ondelete='cascade')
    merge_with_branch_id = fields.Many2one('scm.repository.branch', 'Merge with')
    merge_subfolder = fields.Char('Place merged sources in')

    @api.one
    @api.constrains('branch_id', 'merge_with_branch_id')
    def _check_branch(self):
        if self.branch_id == self.merge_with_branch_id:
            raise UserError(_("You can't merge the branch with itself!"))
