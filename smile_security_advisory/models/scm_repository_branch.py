# -*- coding: utf-8 -*-

from odoo import api, fields, models


class Branch(models.Model):
    _inherit = 'scm.repository.branch'

    security_advisory_ids = fields.One2many(
        'scm.repository.branch.security_advisory', 'branch_id',
        'Security advisories', readonly=True)
    security_advisories_count = fields.Integer(
        compute='_get_security_advisories_count')
    security_advisories_to_apply_count = fields.Integer(
        compute='_get_security_advisories_count')
    security_advisories_to_apply_ratio = fields.Char(
        compute='_get_security_advisories_count')

    @api.one
    @api.depends('security_advisory_ids')
    def _get_security_advisories_count(self):
        self.security_advisories_count = len(self.security_advisory_ids)
        self.security_advisories_to_apply_count = len(
            self.security_advisory_ids.filtered(
                lambda advisory: not advisory.applied))
        self.security_advisories_to_apply_ratio = '%s / %s' % \
            (self.security_advisories_to_apply_count,
             self.security_advisories_count)


class ScmRepositoryBranchSecurityAdvisory(models.Model):
    _name = 'scm.repository.branch.security_advisory'
    _description = 'Security Advisory status by branch'
    _rec_name = 'branch_id'

    security_advisory_id = fields.Many2one(
        'scm.security_advisory', 'Security Advisory',
        required=True, readonly=True, ondelete='cascade')
    severity_level = fields.Selection(
        related='security_advisory_id.severity_level',
        readonly=True)
    branch_id = fields.Many2one(
        'scm.repository.branch', 'Branch',
        required=True, readonly=True, ondelete='cascade')
    applied = fields.Boolean(readonly=True)

    @api.one
    def toggle_apply(self):
        self.applied = not self.applied
