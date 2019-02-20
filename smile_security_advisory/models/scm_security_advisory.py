# -*- coding: utf-8 -*-

from odoo import api, fields, models


class OdooSecurityAdvisory(models.Model):
    _name = 'scm.security_advisory'
    _description = 'Security Advisory'

    name = fields.Char(required=True)
    description = fields.Text(required=True)
    severity_level = fields.Selection([
        ('critical', 'Critical'),
        ('high', 'High'),
        ('medium', 'Medium'),
        ('low', 'Low'),
    ], required=True)
    version_ids = fields.Many2many(
        'scm.version', string='Affected versions', required=True)
    branch_ids = fields.One2many(
        'scm.repository.branch.security_advisory', 'security_advisory_id',
        'Affected branches', readonly=True)
    branches_count = fields.Integer(compute='_get_branches_count')

    _sql_constraints = [
        ("unique_name", "UNIQUE(name)",
         "The security advisory name must be unique"),
    ]

    @api.one
    @api.depends('branch_ids')
    def _get_branches_count(self):
        self.branches_count = len(self.branch_ids) 

    @api.model
    def create(self, vals):
        record = super(OdooSecurityAdvisory, self).create(vals)
        if 'version_ids' in vals:
            record._add_advisories()
        return record

    @api.multi
    def write(self, vals):
        res = super(OdooSecurityAdvisory, self).write(vals)
        if 'version_ids' in vals:
            self._add_advisories()
        return res

    @api.one
    def _add_advisories(self):
        self.branch_ids.filtered(
            lambda advisory:
            advisory.branch_id.version_id not in self.version_ids). \
            unlink()
        for branch in self.env['scm.repository.branch'].search([
            ('version_id', 'in', self.version_ids.ids),
            ('id', 'not in', self.branch_ids.mapped('branch_id').ids),
        ]):
            self.branch_ids.create({
                'security_advisory_id': self.id,
                'branch_id': branch.id,
            })
