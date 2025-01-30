# -*- coding: utf-8 -*-
# (C) 2021 Smile (<http://www.smile.fr>)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import models


class BaseModel(models.AbstractModel):
    _inherit = 'base'

    def nested_read(self, fields=None, load='_classic_read'):
        """
            This methods aim to provide nested reading with performances close
            to native reading.
            Its primary purpose is to be called through RPC.
            If you do not need nested reading, you should use
            native read method.
            The main goal is to reduce the number of rpc read
            calls in order to minimze the weight of the network.
            Usage:
                the argument fields is a dictionary that can contain:
                    -  'fields':<LIST of String> -> Contains a list of fields
                    you want to read from this recordset.
                    - 'field_name': []|null|False -> Read all fields of
                    recordset in field_name.
                    - 'field_name': <Dict> -> Contains a sub dictionary of same
                    format. This will call nested_read for the record
                    associated to this field
            Result will be a list of dictionaries (one per recordset), where
            each read field will either be a value, a tuple or list
            (for relational fields read natively) or a list of dictionaries.
            Example:
                Fields: {
                    'fields': ['name', 'birthdate', 'company_id'],
                    'invoice_ids': {
                        'fields': ['invoice_date', 'ref']
                    }
                }
                Result: [{
                    'name': 'XXX',
                    'birthdate': 'XXXX-XX-XX',
                    'company_id': (XX, <display_name>),
                    'invoice_ids': [
                        {
                            'invoice_date': 'XXXX-XX-XX',
                            'ref': 'XXXX'
                        },
                        {
                            'invoice_date': 'XXXX-XX-XX',
                            'ref': 'XXXX'
                        }
                    ]
                }]
        """
        # Native read
        if not fields or isinstance(fields, list):
            return self.read(fields=fields, load=load)
        if not isinstance(fields, dict):
            raise ValueError("Fields should be a empty, a list or an array.")
        # Fetch the value of the fields we want to read on this record
        fields_to_read = fields.get('fields', [])
        fields_to_read += [f for f in fields.keys() if f != 'fields']
        result = self.read(fields=fields_to_read, load=load)
        for rec_field, sub_fields in fields.items():
            if rec_field == 'fields':
                continue
            for sub_result in result:
                if isinstance(sub_result[rec_field], tuple):
                    sub_rec = self.env[self._fields[rec_field].comodel_name]\
                        .browse(sub_result[rec_field][0])
                else:
                    sub_rec = self.env[self._fields[rec_field].comodel_name] \
                        .browse(sub_result[rec_field])
                sub_result[rec_field] = sub_rec.nested_read(
                    fields=sub_fields, load=load)
        return result
