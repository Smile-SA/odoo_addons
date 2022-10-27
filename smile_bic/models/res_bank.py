# -*- coding: utf-8 -*-
# (C) 2019 Smile (<http://www.smile.fr>)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

import re

from odoo import api, models, _
from odoo.exceptions import ValidationError


class Bank(models.Model):
    _inherit = 'res.bank'

    @api.constrains('bic')
    def _check_bic(self):
        # INFO: ISO 9362:2009
        self.ensure_one()
        bic_check = re.compile(r'^[A-Z]{4}[A-Z]{2}[A-Z0-9]{2}([A-Z0-9]{3})?$')
        if not bic_check.match(self.bic or ''):
            raise ValidationError(_('Incorrect BIC/SWIFT'))
