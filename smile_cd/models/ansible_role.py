# -*- coding: utf-8 -*-

import os.path
import shutil

from odoo import api, fields, models


class AnsibleRole(models.Model):
    _name = "ansible.role"
    _description = "Ansible Role"

    @api.one
    @api.depends("vcs_id", "url")
    def _get_active(self):
        self.active = self.vcs_id and self.url

    @api.one
    def _get_directory(self):
        parent_path = self.env["ansible.deployment"].deployments_path
        self.directory = os.path.join(parent_path, "role_%s" % self.id)

    name = fields.Char(required=True)
    active = fields.Boolean(compute="_get_active", store=True)
    vcs_id = fields.Many2one(
        "scm.vcs", "Version Control System", ondelete="restrict")
    url = fields.Char(size=256)
    branch = fields.Char()
    directory = fields.Char(compute="_get_directory")
    vars = fields.Text("Default variables")
    is_odoo = fields.Boolean()
    package_ids = fields.One2many(
        "scm.version.package",
        "ansible_role_id",
        "Supported Odoo versions/Operating systems",
        copy=False,
    )

    _sql_constraints = [
        ("unique_name", "UNIQUE(name)", "Ansible role name must be unique")
    ]

    @api.model
    def create(self, vals):
        role = super(AnsibleRole, self).create(vals)
        if role.url:
            role.download_sources()
        return role

    @api.multi
    def write(self, vals):
        res = super(AnsibleRole, self).write(vals)
        if "url" in vals or "branch" in vals:
            self.download_sources(remove_if_exists=True)
        return res

    @api.multi
    def download_sources(self, remove_if_exists=False):
        for role in self:
            if not role.vcs_id:
                continue
            directory_exists = os.path.exists(self.directory)
            if remove_if_exists and directory_exists:
                shutil.rmtree(self.directory)
                directory_exists = False
            if directory_exists:
                role.vcs_id.pull(self.directory, role.branch)
            else:
                role.vcs_id.clone(self.directory, role.url, role.branch)
        return True
