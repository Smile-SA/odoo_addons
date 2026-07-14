import json
from unittest.mock import patch, MagicMock
from odoo.tests.common import TransactionCase


class TestWebserviceCall(TransactionCase):
    def setUp(self):
        super(TestWebserviceCall, self).setUp()
        self.webservice_call = self.env['webservice.call'].create({
            'name': 'Test Webservice',
            'url': 'http://example.com/api',
            'type_request': 'get',
            'header': '{}',
            'parameter': '{}',
            'webservice_based_on': 'json',
        })

    def test_00_webservice_call_creation(self):
        self.assertEqual(self.webservice_call.name, 'Test Webservice')
        self.assertEqual(self.webservice_call.url, 'http://example.com/api')
        self.assertEqual(self.webservice_call.type_request, 'get')
        self.assertEqual(self.webservice_call.header, '{}')
        self.assertEqual(self.webservice_call.parameter, '{}')
        self.assertEqual(self.webservice_call.webservice_based_on, 'json')

    @patch('requests.Session.get')
    @patch('odoo.addons.smile_webservice.models.webservice_call.WebserviceCall._cr',  # noqa: E501
           new_callable=MagicMock)
    def test_01_call_request_success(self, mock_cr, mock_get):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {'key': 'value'}
        mock_get.return_value = mock_response

        response = self.webservice_call.call_request()

        self.assertEqual(self.webservice_call.state, 'done')
        self.assertEqual(json.loads(self.webservice_call.response.replace("'", '"')), {'key': 'value'})  # noqa: E501
        self.assertEqual(response, {'key': 'value'})

    @patch('requests.Session.post')
    @patch('odoo.addons.smile_webservice.models.webservice_call.WebserviceCall._cr',  # noqa: E501
           new_callable=MagicMock)
    def test_02_call_request_post_success(self, mock_cr, mock_post):
        self.webservice_call.type_request = 'post'
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {'key': 'value'}
        mock_post.return_value = mock_response

        response = self.webservice_call.call_request()

        self.assertEqual(self.webservice_call.state, 'done')
        self.assertEqual(
            json.loads(
                self.webservice_call.response.replace("'", '"')),
            {'key': 'value'})
        self.assertEqual(response, {'key': 'value'})

    @patch('requests.Session.put')
    @patch('odoo.addons.smile_webservice.models.webservice_call.WebserviceCall._cr',  # noqa: E501
           new_callable=MagicMock)
    def test_03_call_request_put_success(self, mock_cr, mock_put):
        self.webservice_call.type_request = 'put'
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {'key': 'value'}
        mock_put.return_value = mock_response

        response = self.webservice_call.call_request()

        self.assertEqual(self.webservice_call.state, 'done')
        self.assertEqual(json.loads(self.webservice_call.response.replace("'", '"')), {'key': 'value'})  # noqa: E501
        self.assertEqual(response, {'key': 'value'})

    @patch('requests.Session.delete')
    @patch('odoo.addons.smile_webservice.models.webservice_call.WebserviceCall._cr',  # noqa: E501
           new_callable=MagicMock)
    def test_04_call_request_delete_success(self, mock_cr, mock_delete):
        self.webservice_call.type_request = 'delete'
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {'key': 'value'}
        mock_delete.return_value = mock_response

        response = self.webservice_call.call_request()

        self.assertEqual(self.webservice_call.state, 'done')
        self.assertEqual(json.loads(self.webservice_call.response.replace("'", '"')), {'key': 'value'})  # noqa: E501
        self.assertEqual(response, {'key': 'value'})

    def test_05_action_reset_to_draft(self):
        self.webservice_call.state = 'done'
        self.webservice_call.action_reset_to_draft()
        self.assertEqual(self.webservice_call.state, 'draft')

    def test_06_action_in_progress(self):
        self.webservice_call.state = 'draft'
        self.webservice_call.action_in_progress()
        self.assertEqual(self.webservice_call.state, 'in_progress')

    def test_07_action_force_done(self):
        self.webservice_call.state = 'in_progress'
        self.webservice_call.action_force_done()
        self.assertEqual(self.webservice_call.state, 'done')

    def test_08_retry_error(self):
        self.webservice_call.state = 'error'
        self.webservice_call.retry_error()
        self.assertEqual(self.webservice_call.state, 'done')

    def test_09_access_value_from_dict(self):
        dict_response = {'root': {'child': 'value'}}
        expected_response_list = ['root', 'child']
        result = self.webservice_call.access_value_from_dict(
            expected_response_list, dict_response)
        self.assertEqual(result, 'value')

    def test_10_get_webservice_based_on(self):
        self.webservice_call.webservice_based_on = 'context'
        self.webservice_call = self.webservice_call.with_context(
            webservice_based_on='xml')
        result = self.webservice_call._get_webservice_based_on()
        self.assertEqual(result, 'xml')
