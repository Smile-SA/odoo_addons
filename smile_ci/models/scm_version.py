# -*- coding: utf-8 -*-

from odoo import fields, models


class OdooVersion(models.Model):
    _inherit = 'scm.version'

    server_cmd = fields.Char('Server command', required=True, default='odoo.py')
    package_ids = fields.One2many('scm.version.package', 'version_id', 'Packages')
    web_included = fields.Boolean('Web Included', default=True)
    standard_xmlrpc = fields.Boolean('Standard XML/RPC', default=True)
