# -*- coding: utf-8 -*-
# (C) 2021 Smile (<http://www.smile.fr>)
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl).
import json
import xmltodict
from ast import literal_eval
import logging
from odoo import fields, models, api, exceptions, _
from odoo.addons.smile_webservice.models.webservice_error import WebserviceError
from odoo.exceptions import ValidationError
from odoo.tools import safe_eval

_logger = logging.getLogger(__name__)

LIST_STATE = [
    ('draft', 'Draft'),
    ('in_progress', 'In progress'),
    ('done', 'Done'),
    ('error', 'Error'),
]


class WebserviceCall(models.Model):
    _name = 'webservice.call'
    _description = 'Webservices'

    name = fields.Char(string='Name', required=True)
    # To override in specific modules : one webservice_type for each type of webservice
    webservice_type = fields.Selection(selection=[], string='Webservice type')
    webservice_model = fields.Selection(string='Model', selection=[])
    state = fields.Selection(LIST_STATE, string='State', default='draft')
    is_verify_ssl = fields.Boolean(string='SSL verification ?', default=True)

    header = fields.Text(string='Header')
    type_request = fields.Selection(string='Type request',
                                    selection=[('get', 'GET'), ('post', 'POST'), ('put', 'PUT'),
                                               ('delete', 'DELETE')], default='get')

    url = fields.Text(string='URL call')
    parameter = fields.Text(string='Parameter')
    response = fields.Text(string='Response')

    error_code = fields.Char(string='Error code')
    error_message = fields.Text(string='Error message')

    webservice_based_on = fields.Selection(selection=[('json', 'JSON'), ('xml', 'XML')], string='Based on',
                                           default='json')
    expected_response = fields.Char(string='Expected response')
    xml_namespaces = fields.Char(string='XML namespaces')
    converted_response = fields.Char(string='Converted response')
    duration = fields.Integer(string='Duration (s)')

    @api.constrains('expected_response')
    def check_expected_response_data_structure(self):
        for line in self:
            expected_response = line.expected_response
            if expected_response:
                expected_response = safe_eval(expected_response)
                if not isinstance(expected_response, dict):
                    raise exceptions.ValidationError(
                        _("The expected response should be a dictionary [%s, id:%s]") % (line.name, line.id))

    @api.constrains('xml_namespaces')
    def check_xml_namespaces_data_structure(self):
        for line in self:
            xml_namespaces = line.xml_namespaces
            if xml_namespaces:
                xml_namespaces = safe_eval(xml_namespaces)
                if not isinstance(xml_namespaces, dict):
                    raise exceptions.ValidationError(
                        _("The xml namespaces should be a dictionary [%s, id:%s]") % (line.name, line.id))

    def action_reset_to_draft(self):
        self.write({'state': 'draft'})

    def action_re_try(self):
        self.call_request()

    def action_in_progress(self):
        self.write({'state': 'in_progress'})

    def action_force_done(self):
        self.write({'state': 'done'})

    def retry_error(self):
        self.search([('state', '=', 'error')]).action_force_done()

    def call_request(self):
        converted_response = ''
        resp_acquired = False
        self.write({'state': 'in_progress'})
        self._cr.commit()
        try:
            resp = self.execute_call()
            resp_acquired = True
            resp.raise_for_status()
        except Exception as e:
            # If resp is a <Reponse [500]>, then resp is considered False, so we can't do something like "resp and ..."
            error_message = '%s\n%s' % (e.args[0], resp_acquired and resp.text and str(resp.text) or '')
            self.write({'state': 'error',
                        'error_code': resp_acquired and resp and resp.status_code or '',
                        'error_message': error_message})
            self._cr.commit()
            raise WebserviceError(error_message)
        try:
            response = self.format_response(resp)
            converted_response = self.convert_response(response)
        except Exception:
            response = resp.text
        duration = (fields.Datetime.now() - self.create_date).total_seconds()
        self.write({'response': response, 'converted_response': converted_response,
                    'state': 'done', 'duration': duration})
        return converted_response or response

    def execute_call(self):
        resp = ''
        webservice_session = self._retrieve_webservice_session()
        timeout = self._get_webservice_timeout()
        if self.webservice_based_on == 'json':
            if self.type_request == 'post':
                resp = webservice_session.post(url=self.url, json=self.parameter and json.loads(self.parameter) or '',
                                               headers=literal_eval(self.header),
                                               verify=self.is_verify_ssl, timeout=timeout)
            elif self.type_request == 'get':
                resp = webservice_session.get(url=self.url, params=self.parameter and json.loads(self.parameter) or '',
                                              headers=literal_eval(self.header),
                                              verify=self.is_verify_ssl, timeout=timeout)
            elif self.type_request == 'put':
                resp = webservice_session.put(url=self.url, json=self.parameter and json.loads(self.parameter) or '',
                                              headers=literal_eval(self.header),
                                              verify=self.is_verify_ssl, timeout=timeout)
            elif self.type_request == 'delete':
                resp = webservice_session.delete(url=self.url, json=self.parameter and json.loads(self.parameter) or '',
                                                 headers=literal_eval(self.header),
                                                 verify=self.is_verify_ssl, timeout=timeout)
        elif self.webservice_based_on == 'xml':
            if self.type_request == 'post':
                resp = webservice_session.post(url=self.url, data=self.parameter,
                                               headers=literal_eval(self.header), verify=self.is_verify_ssl,
                                               timeout=timeout)
            elif self.type_request == 'get':
                resp = webservice_session.get(url=self.url, data=self.parameter,
                                              headers=literal_eval(self.header), verify=self.is_verify_ssl,
                                              timeout=timeout)
        return resp

    def format_response(self, resp):
        if self.webservice_based_on == 'json':
            response = resp.json()
        elif self.webservice_based_on == 'xml':
            response = resp.content
        else:
            response = resp
        return response

    def convert_response(self, response):
        converted_response = ""
        if self.webservice_based_on == 'xml' and self.expected_response and response:
            converted_response = self.convert_xml_response(response)
        return converted_response

    def _retrieve_webservice_session(self):
        """" if session is not in the context , generate a new one """
        return self.env.context.get('webservice_session') or self._generate_webservice_authenticate()

    def update_error(self, error_message):
        self.write({'state': 'error', 'error_message': error_message})

    @api.model
    def raise_error_if_not_from_cron(self, error_msg):
        _logger.error(error_msg)
        if self:
            self.update_error(error_msg)
        if not self._context.get('with_cron'):
            raise ValidationError(error_msg)

    def _check_webservice_state(self):
        if self.state != 'done':
            if self._context.get('retry'):
                return False
            else:
                self.raise_error_if_not_from_cron(_('The Webservice (id: %s) call failed.') % self.id)
        else:
            return True

    @api.model
    def convert_xml_response(self, response):
        expected_response = self.expected_response
        xml_namespaces = self.xml_namespaces
        if not expected_response:
            return response
        res = {}
        if expected_response:
            expected_response = safe_eval(expected_response)
        if xml_namespaces:
            xml_namespaces = safe_eval(xml_namespaces)
        if xml_namespaces and not isinstance(xml_namespaces, dict):
            raise exceptions.ValidationError(_('The xml_namespaces should be a dictionary'))
        if not isinstance(expected_response, dict):
            raise exceptions.ValidationError(_('The expect response should be a dictionary'))
        dict_response = xmltodict.parse(response, process_namespaces=True, namespaces=xml_namespaces)
        for expected_key in expected_response:
            expected_key_path = expected_response[expected_key].split('/')
            res[expected_key] = self.access_value_from_dict(expected_key_path, dict_response)
        return res

    @api.model
    def access_value_from_dict(self, expected_response_list, dict_response):
        item_to_search = expected_response_list[0]
        if item_to_search not in dict_response:
            return ''
        value = dict_response[item_to_search]
        if len(expected_response_list) == 1:
            return value
        expected_response_list.pop(0)
        return self.access_value_from_dict(expected_response_list, value)
