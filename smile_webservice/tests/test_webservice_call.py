import json
from datetime import timedelta
from unittest.mock import patch, MagicMock
import requests
from odoo import Command, fields
from odoo.addons.smile_webservice.models.webservice_error import (
    WebserviceError,
)
from odoo.exceptions import AccessError
from odoo.tests.common import TransactionCase


class TestWebserviceCall(TransactionCase):
    def setUp(self):
        super().setUp()
        # Odoo 20: TransactionCase forbids commit by patching the cursor
        # instance, so the commit done by call_request must be patched there.
        self.startPatcher(patch.object(self.env.cr, 'commit'))
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
    def test_01_call_request_success(self, mock_get):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {'key': 'value'}
        mock_get.return_value = mock_response

        response = self.webservice_call.call_request()

        self.assertEqual(self.webservice_call.state, 'done')
        self.assertEqual(json.loads(self.webservice_call.response.replace("'", '"')), {'key': 'value'})  # noqa: E501
        self.assertEqual(response, {'key': 'value'})

    @patch('requests.Session.post')
    def test_02_call_request_post_success(self, mock_post):
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
    def test_03_call_request_put_success(self, mock_put):
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
    def test_04_call_request_delete_success(self, mock_delete):
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

    @patch('requests.Session.get')
    def test_08_retry_error(self, mock_get):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {'key': 'value'}
        mock_get.return_value = mock_response
        self.webservice_call.state = 'error'
        self.webservice_call.retry_error()
        self.assertEqual(self.webservice_call.state, 'done')
        self.assertTrue(self.webservice_call.response)

    @patch('requests.Session.get')
    def test_08b_retry_error_still_failing(self, mock_get):
        mock_get.side_effect = requests.ConnectionError('boom')
        self.webservice_call.state = 'error'
        self.webservice_call.retry_error()
        self.assertEqual(self.webservice_call.state, 'error')

    @patch('requests.Session.get')
    def test_11_call_request_network_error(self, mock_get):
        mock_get.side_effect = requests.ConnectionError('boom')
        # Odoo's assertRaises rolls back to a savepoint, which would undo
        # the 'error' state written (and committed) before raising.
        try:
            self.webservice_call.call_request()
        except WebserviceError:
            pass
        else:
            self.fail('WebserviceError not raised')
        self.assertEqual(self.webservice_call.state, 'error')

    @patch('requests.Session.get')
    def test_12_empty_header(self, mock_get):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {'key': 'value'}
        mock_get.return_value = mock_response
        self.webservice_call.header = False
        self.webservice_call.call_request()
        self.assertEqual(self.webservice_call.state, 'done')

    def test_13_ensure_one(self):
        calls = self.webservice_call | self.webservice_call.copy()
        with self.assertRaises(ValueError):
            calls.call_request()

    @patch('requests.Session.get')
    def test_14_duration_independent_of_create_date(self, mock_get):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {'key': 'value'}
        mock_get.return_value = mock_response
        self.env.cr.execute(
            "UPDATE webservice_call SET create_date = %s WHERE id = %s",
            (fields.Datetime.now() - timedelta(days=1),
             self.webservice_call.id))
        self.webservice_call.invalidate_recordset()
        self.webservice_call.call_request()
        self.assertLess(self.webservice_call.duration, 60)

    def test_15_access(self):
        vals = {'name': 'ACL', 'url': 'http://example.com'}
        user = self.env['res.users'].create({
            'name': 'Simple user', 'login': 'ws_simple',
            'group_ids': [Command.set([self.env.ref('base.group_user').id])],
        })
        with self.assertRaises(AccessError):
            self.env['webservice.call'].with_user(user).create(vals)
        manager = self.env['res.users'].create({
            'name': 'ERP manager', 'login': 'ws_manager',
            'group_ids': [Command.set(
                [self.env.ref('base.group_erp_manager').id])],
        })
        call = self.env['webservice.call'].with_user(manager).create(vals)
        self.assertTrue(call.read(['name']))

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
