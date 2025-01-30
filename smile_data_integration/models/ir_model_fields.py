# -*- coding: utf-8 -*-
# (C) 2020 Smile (<https://www.smile.eu>)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import models, api


class IrModelFields(models.Model):
    _inherit = 'ir.model.fields'

    @api.model
    def _is_manual_name(self, name):
        '''
            Odoo added a check on fields name to prevent creating field not starting with 'x_'.
            We extend the method to allow creating the 'old_id' field
            without the 'x_' prefix.
        '''
        return super()._is_manual_name(name) \
            if not self.env.context.get('smile_data_integration') else True
