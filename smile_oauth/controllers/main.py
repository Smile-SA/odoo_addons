# -*- coding: utf-8 -*-
# (C) 2022 Smile (<https://www.smile.eu>)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

import json
import werkzeug.urls

from odoo.http import request
from odoo.addons.auth_oauth.controllers.main import OAuthLogin as Home


class SmileOAuthLogin(Home):
    def list_providers(self):
        providers = super(SmileOAuthLogin, self).list_providers()
        for provider_values in providers:
            oauth_provider = request.env['auth.oauth.provider'].browse(
                provider_values.get('id'))
            if oauth_provider.use_authorization_code_flow:
                return_url = request.httprequest.url_root + 'auth_oauth/signin'
                state = self.get_state(provider_values)
                params = {
                    'response_type': 'code',
                    'client_id': oauth_provider.client_id,
                    'redirect_uri': return_url,
                    'scope': oauth_provider.scope,
                    'state': json.dumps(state),
                }
                if oauth_provider.use_pkce:
                    code_verifier, code_challenge = \
                        oauth_provider._generate_pkce_pair(
                            request.session.get('oauth_code_verifier'))
                    params.update({
                        'code_challenge': code_challenge,
                        'code_challenge_method': 'S256',
                    })
                    # Store code verifier
                    request.session['oauth_code_verifier'] = code_verifier
                provider_values['auth_link'] = \
                    "%s?%s" % (provider_values['auth_endpoint'],
                               werkzeug.urls.url_encode(params))
        return providers
