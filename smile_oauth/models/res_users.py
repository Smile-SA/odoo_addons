# -*- coding: utf-8 -*-
# (C) 2022 Smile (<https://www.smile.eu>)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

import json
import requests

from odoo import api, models
from odoo.tools.safe_eval import safe_eval
from odoo.http import request
from odoo.exceptions import AccessDenied, UserError
from odoo.addons.auth_signup.models.res_users import SignupError


def eval_proxies(proxies):
    try:
        proxies = safe_eval(proxies)
        if isinstance(proxies, dict):
            return proxies
        return None
    except Exception:
        return None


class ResUsers(models.Model):
    _inherit = 'res.users'

    @api.model
    def _auth_oauth_request_code(self, endpoint, params, proxies=None):
        if proxies:
            proxies = eval_proxies(proxies)
        return requests.post(endpoint, data=params, proxies=proxies).json()

    @api.model
    def _auth_oauth_request_userinfo(
            self, endpoint, access_token, token_type='Bearer', proxies=None):
        if proxies:
            proxies = eval_proxies(proxies)
        headers = {'Authorization': '{} {}'.format(token_type, access_token)}
        return requests.post(endpoint, headers=headers, proxies=proxies).json()

    @api.model
    def _auth_oauth_validate_code(self, provider, code):
        oauth_provider = self.env['auth.oauth.provider'].browse(provider)
        return_url = request.httprequest.url_root + 'auth_oauth/signin'
        params = {
            'client_id': oauth_provider.client_id,
            'redirect_uri': return_url,
            'grant_type': 'authorization_code',
            'code': code,
        }
        if oauth_provider.client_secret:
            params.update({'client_secret': oauth_provider.client_secret})
        if oauth_provider.use_pkce:
            params.update({
                'code_verifier': request.session.get('oauth_code_verifier')})
        validation = self._auth_oauth_request_code(
            oauth_provider.validation_endpoint, params, oauth_provider.proxies)
        if validation.get("error"):
            raise Exception(validation['error'])
        access_token = validation.get('access_token')
        if not access_token:
            raise AccessDenied()
        if oauth_provider.data_endpoint:
            data = self._auth_oauth_request_userinfo(
                oauth_provider.data_endpoint, access_token,
                validation.get('token_type'), oauth_provider.proxies)
            validation.update(data)
        # Clear code verifier
        request.session['oauth_code_verifier'] = None
        return validation

    @api.model
    def auth_oauth(self, provider, params):
        oauth_provider = self.env['auth.oauth.provider'].browse(provider)
        if oauth_provider.use_authorization_code_flow:
            code = params.get('code')
            if not code:
                raise AccessDenied()
            validation = self._auth_oauth_validate_code(provider, code)
            access_token = validation.get('access_token')
            params.update({'access_token': access_token})
            # required check
            if not validation.get('user_id'):
                if validation.get('sub'):
                    validation['user_id'] = validation['sub']
                else:
                    raise AccessDenied()
            # retrieve and sign in user
            login = self._auth_oauth_signin(provider, validation, params)
            if not login:
                raise AccessDenied()
            # return user credentials
            return (self.env.cr.dbname, login, access_token)
        return super().auth_oauth(provider, params)

    @api.model
    def _auth_oauth_signin_by_mail(self, provider, validation, params):
        oauth_email = validation['email']
        oauth_uid = validation['user_id']
        try:
            oauth_user = self.search([
                ('login', '=', oauth_email),
                ('oauth_provider_id', '=', provider)
            ])
            if not oauth_user:
                raise AccessDenied()
            assert len(oauth_user) == 1
            oauth_user.write({
                'oauth_uid': oauth_uid,
                'oauth_access_token': params['access_token']
            })
            return oauth_user.login
        except AccessDenied as access_denied_exception:
            if self.env.context.get('no_user_creation'):
                return None
            state = json.loads(params['state'])
            token = state.get('t')
            values = self._generate_signup_values(provider, validation, params)
            try:
                _, login, _ = self.signup(values, token)
                return login
            except (SignupError, UserError):
                raise access_denied_exception

    @api.model
    def _auth_oauth_signin(self, provider, validation, params):
        try:
            return super()._auth_oauth_signin(provider, validation, params)
        except AccessDenied:
            try:
                return self._auth_oauth_signin_by_mail(
                    provider, validation, params)
            except AccessDenied as access_denied_exception:
                raise access_denied_exception
