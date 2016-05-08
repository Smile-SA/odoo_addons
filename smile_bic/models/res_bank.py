# -*- coding: utf-8 -*-

import re

from openerp import api, models, _
from openerp.exceptions import UserError


class ResBank(models.Model):
    _inherit = 'res.bank'

    @api.one
    @api.constrains('bic')
    def _check_bic(self):
        # ISO 9362:2009
        bic_check = re.compile(r'^[A-Z]{4}[A-Z]{2}[A-Z0-9]{2}([A-Z0-9]{3})?$')
        if self.bic and not bic_check.match(self.bic):
            raise UserError(_('Incorrect BIC/SWIFT'))
