# (C) 2023 Smile (<http://www.smile.fr>)
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl).

import hashlib
import json

from odoo import models, tools
from odoo.addons.website.models.ir_qweb import AssetsBundleMultiWebsite
from odoo.tools import func




class SmileAssetsVersionBundle(AssetsBundleMultiWebsite):

    @func.lazy_property
    def checksum(self):
        def old_checksum():
            check = u"%s%s" % (json.dumps(self.files, sort_keys=True), self.last_modified_combined)
            return hashlib.sha512(check.encode('utf-8')).hexdigest()[:64]
        if tools.config.get('server_environment', False) in \
                ['preprod', 'prod']:
            code_version = \
                self.env['ir.config_parameter'].sudo().get_param('code.version')
            if code_version:
                return hashlib.sha1(code_version.encode('utf-8')).hexdigest()
        return old_checksum()


class IrQweb(models.AbstractModel):
    _inherit = 'ir.qweb'
    def _get_asset_bundle(self, xmlid, files, env=None, css=True, js=True):
        return SmileAssetsVersionBundle(xmlid, files, env=env)
