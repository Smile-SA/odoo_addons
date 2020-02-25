# (C) 2019 Smile (<http://www.smile.fr>)
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl).

from odoo import models


class IrHttp(models.AbstractModel):

    _inherit = 'ir.http'

    def session_info(self):
        result = super().session_info()
        result['has_group_smile_import'] = self.env.user.has_group('smile_web_impex.group_import')
        result['has_group_smile_export'] = self.env.user.has_group('smile_web_impex.group_export')
        return result
