# -*- coding: utf-8 -*-

from odoo import fields, models


class OdooVersionPackage(models.Model):
    _name = 'scm.version.package'
    _description = 'Packages by Odoo Version and Operating System'
    _rec_name = 'os_id'
    _order = 'os_id, version_id'

    version_id = fields.Many2one('scm.version', 'Odoo Version', required=True, ondelete='cascade')
    os_id = fields.Many2one('scm.os', 'Operating System', required=True, ondelete='cascade')
    system_packages = fields.Text('System packages')
    pip_packages = fields.Text('PyPI packages')
    npm_packages = fields.Text('Node.js packages')
