# -*- coding: utf-8 -*-
# (C) 2021 Smile (<http://www.smile.fr>)
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl).

import requests
from odoo import api, models
from odoo.tools import config as odoo_instance_config


class BaseModel(models.AbstractModel):
    _inherit = 'base'

    def _get_webservice_call(self, webservice_type, type_request, name, url, parameter=None, **kwargs):
        webservice_call = self._context.get('webservice_call')
        if not webservice_call:
            datas = self._prepare_webservice_call(webservice_type, type_request, name, url,
                                                  parameter=parameter, **kwargs)
            if datas:
                webservice_call = self.env['webservice.call'].create(datas)
        return webservice_call

    def _prepare_webservice_call(self, webservice_type, type_request, name, url, parameter=None, **kwargs):
        datas = {
            'webservice_type': webservice_type,
            'type_request': type_request,
            'name': name,
            'parameter': parameter,
            'url': url,
        }
        datas.update(kwargs)
        return datas

    @api.model
    def _generate_webservice_authenticate(self):
        authentication_data = self._get_authentication_data()
        login, password = authentication_data.get('login'), authentication_data.get('password')
        session = requests.Session()
        session.auth = (login, password)
        return session

    @api.model
    def _get_authentication_data(self):
        """To be inherited in the other models"""
        return {'login': '', 'password': ''}

    @api.model
    def _get_webservice_timeout(self):
        return int(odoo_instance_config.get('webservice_call_timeout', 60))
