# -*- encoding: utf-8 -*-
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2020 Smile (<http://www.smile.fr>). All Rights Reserved
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#

from odoo import api, models, fields


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

        json_elt = eval(self.json_element)
        for elt in elt_list:
            if elt == '_first_child':
                json_elt = json_elt[json_elt.keys()[0]]
            else:
                if json_elt.get(elt):
                    json_elt = json_elt[elt]
                else:
                    return sub_val
        return json_elt
