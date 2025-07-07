from odoo import models, api, tools
from odoo.addons.base.models.assetsbundle import AssetsBundle
import hashlib


class CustomAssetsBundle(AssetsBundle):
    def get_checksum(self, asset_type):
        if tools.config.get('server_environment', False) in \
                ['preprod', 'prod']:
            code_version = (
                self.env["ir.config_parameter"]
                .sudo()
                .get_param("code.version")
            )
            if code_version:
                return hashlib.sha1(code_version.encode()).hexdigest()[:64]

        return super().get_checksum(asset_type)


class IrQweb(models.AbstractModel):
    _inherit = 'ir.qweb'

    @api.model
    def _get_asset_bundle(self, bundle_name, css=True, js=True,
                          debug_assets=False, rtl=False, assets_params=None):
        if assets_params is None:
            assets_params = self.env['ir.asset']._get_asset_params()
        files, external_assets = self._get_asset_content(
            bundle_name, assets_params
        )
        return CustomAssetsBundle(
            bundle_name,
            files,
            external_assets,
            env=self.env,
            css=css,
            js=js,
            debug_assets=debug_assets,
            rtl=rtl,
            assets_params=assets_params,
        )
