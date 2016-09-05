# -*- coding: utf-8 -*-

from odoo import fields, models


class VersionControlSystem(models.Model):
    _name = 'scm.vcs'
    _description = 'Version Control System'

    name = fields.Char(required=True)
    cmd = fields.Char('Command', size=3, required=True)
    cmd_clone = fields.Char('Clone', required=True)
    cmd_pull = fields.Char('Pull', required=True)
    default_branch = fields.Char('Default branch')

    _sql_constraints = [
        ('unique_cmd', 'UNIQUE(cmd)', 'VCS must be unique'),
    ]
