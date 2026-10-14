# -*- coding: utf-8 -*-
# (C) 2025 Smile (<http://www.smile.fr>)
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl).

import json
import logging

from odoo.tests.common import TransactionCase

from odoo.addons.smile_parsejson.models.parse_json_mixin import ParseJsonMixin

_logger = logging.getLogger(__name__)


class TestParseJsonMixin(TransactionCase):
    def setUp(self):
        super().setUp()

        class MockRecord:
            def __init__(self, json_element):
                self.json_element = json_element

        self.mock_record = MockRecord(None)
        self.mock_record.json_get = ParseJsonMixin.json_get.__get__(
            self.mock_record)

        self.json_data = json.dumps({
            "id": 147,
            "idItem": 128161,
            "host": "APITUDE",
            "property": {
                "HS_AFI_H_4864843": {
                    "id": 15392205,
                    "name": "Regency Hotel Miami",
                    "syscode": "HS_AFI_H_4864843"
                }
            }
        })
        self.mock_record.json_element = self.json_data

    def test_01_json_get_valid_path(self):
        """
            Test extracting a value with a valid path.

            Prerequisites:
                - A JSON object with nested properties
                - A valid path to a nested value

            Test:
                - Extract the value using a list
                path ['property', 'HS_AFI_H_4864843', 'name']

            Expected:
                - The extracted value should be 'Regency Hotel Miami'
        """
        result = self.mock_record.json_get(
            ['property', 'HS_AFI_H_4864843', 'name'])
        self.assertEqual(
            result, "Regency Hotel Miami",
            "The extracted value does not correspond to the expected "
            "value.")

    def test_02_json_get_invalid_path(self):
        """
            Test extracting a value with an invalid path.

            Prerequisites:
                - A JSON object with nested properties
                - An invalid path that doesn't exist in the JSON

            Test:
                - Extract the value using a non-existent
                path ['property', 'invalid_key']

            Expected:
                - The extracted value should be None
        """
        result = self.mock_record.json_get(['property', 'invalid_key'])
        self.assertIsNone(
            result,
            "The extracted value should be None for an invalid path.")

    def test_03_json_get_empty_json(self):
        """
            Test extracting a value from an empty JSON.

            Prerequisites:
                - An empty JSON object
                - A path that would be valid in a non-empty JSON

            Test:
                - Extract the value using
                a path ['property', 'HS_AFI_H_4864843', 'name']

            Expected:
                - The extracted value should be None
        """
        self.mock_record.json_element = "{}"
        result = self.mock_record.json_get(
            ['property', 'HS_AFI_H_4864843', 'name'])
        self.assertIsNone(
            result,
            "The extracted value should be None for an empty JSON.")

    def test_04_json_get_with_default(self):
        """
            Test extracting a value with a default value for invalid paths.

            Prerequisites:
                - A JSON object with nested properties
                - An invalid path that doesn't exist in the JSON
                - A default value to return when path is invalid

            Test:
                - Extract the value using a non-existent path
                with a default value

            Expected:
                - The extracted value should be the provided default value 'default_value'
        """
        result = self.mock_record.json_get(['property', 'invalid_key'],
                                           'default_value')
        self.assertEqual(
            result, "default_value",
            "The extracted value should be the default value for an "
            "invalid path.")

    def test_05_json_get_with_comma_path(self):
        """
            Test extracting a value using a comma-separated string path.

            Prerequisites:
                - A JSON object with nested properties
                - A path represented as a comma-separated string

            Test:
                - Extract the value using the string
                path 'property,HS_AFI_H_4864843,name'

            Expected:
                - The extracted value should be 'Regency Hotel Miami'
        """
        result = self.mock_record.json_get(
            'property,HS_AFI_H_4864843,name')
        self.assertEqual(
            result, "Regency Hotel Miami",
            "The value extracted with a comma-separated path does not "
            "correspond to the expected value.")

    def test_06_json_get_direct_value(self):
        """
            Test extracting a direct value from the root level.

            Prerequisites:
                - A JSON object with properties at the root level
                - A valid key at the root level

            Test:
                - Extract the value using a direct key 'id'

            Expected:
                - The extracted value should be 147
        """
        result = self.mock_record.json_get('id')
        self.assertEqual(
            result, 147,
            "The extracted value does not correspond to the expected value.")

    def test_07_json_get_with_list_path(self):
        """
            Test extracting a value using a single-element list path.

            Prerequisites:
                - A JSON object with properties at the root level
                - A valid key at the root level

            Test:
                - Extract the value using a single-element list path ['idItem']

            Expected:
                - The extracted value should be 128161
            """
        result = self.mock_record.json_get(['idItem'])
        self.assertEqual(
            result, 128161,
            "The extracted value does not correspond to the expected value.")

    def test_08_json_get_first_child(self):
        """
            Test '_first_child' goes into the first child element.

            Expected:
                - ['property', '_first_child', 'name'] returns
                'Regency Hotel Miami'
        """
        result = self.mock_record.json_get(['property', '_first_child', 'name'])
        self.assertEqual(result, "Regency Hotel Miami")

    def test_09_json_get_falsy_value(self):
        """
            Test falsy values (0, '', False) are returned, not sub_val.
        """
        self.mock_record.json_element = json.dumps(
            {"zero": 0, "empty": "", "no": False})
        self.assertEqual(self.mock_record.json_get('zero', 'default'), 0)
        self.assertEqual(self.mock_record.json_get('empty', 'default'), "")
        self.assertIs(self.mock_record.json_get('no', 'default'), False)

    def test_10_json_get_python_literal_no_code_execution(self):
        """
            Test Python literals are still parsed, but code is not executed.
        """
        self.mock_record.json_element = "{'a': True, 'b': None}"
        self.assertIs(self.mock_record.json_get('a'), True)
        self.mock_record.json_element = "__import__('os').getcwd()"
        with self.assertRaises(ValueError):
            self.mock_record.json_get('a')
