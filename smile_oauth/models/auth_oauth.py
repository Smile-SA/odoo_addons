# -*- coding: utf-8 -*-
# (C) 2022 Smile (<https://www.smile.eu>)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

import secrets
import base64
import hashlib

from odoo import fields, models


class AuthOAuthProvider(models.Model):
    _inherit = 'auth.oauth.provider'

    use_authorization_code_flow = fields.Boolean()
    client_secret = fields.Char(string='Client Secret')
    use_pkce = fields.Boolean()
    proxies = fields.Char(string='Call URLs via proxies')

    def _generate_pkce_pair(self, code_verifier=None):
        if code_verifier is None:
            code_verifier = secrets.token_urlsafe(96)
        hashed = hashlib.sha256(code_verifier.encode('ascii')).digest()
        encoded = base64.urlsafe_b64encode(hashed)
        code_challenge = encoded.decode('ascii')[:-1]
        return code_verifier, code_challenge
