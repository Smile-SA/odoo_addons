# -*- coding: utf-8 -*-
# (C) 2025 Smile (<http://www.smile.fr>)
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl).

import ast
import json

from odoo import api, models, fields


def _json_parse(json_element):
    # JSON first; Python literals (True, None, single quotes) are still
    # accepted as with the former eval(), without executing code
    try:
        return json.loads(json_element)
    except ValueError:
        return ast.literal_eval(json_element)


class ParseJsonMixin(models.AbstractModel):
    _name = 'parse_json.mixin'
    _description = 'Mixin class for parsing json datas'

    json_element = fields.Text()

    @api.model
    def json_get(self, elt_list, sub_val=None):
        """

        :param json_elt: Json element :
        {
            "id": 147,
            "idItem": 128161,
            "host": "APITUDE",
            "property": {
                "HS_AFI_H_4864843": {
                    "id": 15392205,
                    "name": "Regency Hotel Miami",
                    "syscode": "HS_AFI_H_4864843"
                }
            },
            ...
        :param test_fields: list of fields or DOM parser properties:
        ['property', 'name']
        List of possible DOM parser properties :
            - '_first_child' : go into first child element
        :return: True if fields path is correct
        """
        if isinstance(elt_list, str):
            elt_list = elt_list.split(',')

        json_elt = _json_parse(self.json_element)
        for elt in elt_list:
            if elt == '_first_child':
                json_elt = json_elt[next(iter(json_elt))]
            else:
                if elt in json_elt:
                    json_elt = json_elt[elt]
                else:
                    return sub_val
        return json_elt
