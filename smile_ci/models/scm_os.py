# -*- coding: utf-8 -*-

from odoo import api, fields, models


class OperatingSystem(models.Model):
    _name = 'scm.os'
    _description = 'Operating System'

    name = fields.Char(required=True)
    sequence = fields.Integer(default=10)
    active = fields.Boolean(default=True)
    dockerfile = fields.Binary('Dockerfile template', required=True, help='Used to build Build image')
    dockerfile_base = fields.Binary('Dockerfile base template', help='Used to build Branch base image')
    odoo_dir = fields.Char('Odoo directory', required=True, default='/usr/src/odoo')
    package_ids = fields.One2many('scm.version.package', 'os_id', 'Packages')
    branch_ids = fields.One2many('scm.repository.branch', 'os_id', 'Branches')

    @api.multi
    def write(self, vals):
        result = super(OperatingSystem, self).write(vals)
        if 'dockerfile_base' in vals or 'odoo_dir' in vals:
            self.mapped('branch_ids').force_recreate_image()
        return result
