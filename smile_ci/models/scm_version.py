# -*- coding: utf-8 -*-

from odoo import api, fields, models


class OdooVersion(models.Model):
    _inherit = 'scm.version'

    @api.model
    def _get_default_os(self):
        return self.env['scm.os'].sudo().search([], limit=1)

    server_cmd = fields.Char(
        'Server command', required=True, default='odoo-bin')
    package_ids = fields.One2many(
        'scm.version.package', 'version_id', 'Packages')
    web_included = fields.Boolean('Web Included', default=True)
    standard_xmlrpc = fields.Boolean('Standard XML/RPC', default=True)
    user_uid = fields.Integer('Admin id', default=1, required=True)
    default_os_id = fields.Many2one(
        'scm.os', 'Operating System',
        required=True, default=_get_default_os)
