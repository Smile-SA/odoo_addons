# -*- coding: utf-8 -*-
# (C) 2023 Smile (<https://www.smile.eu>)
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl).
from odoo import models


class BaseModel(models.AbstractModel):
    _inherit = 'base'

    def get_message_informations(self, values=False):
        """
            This function gives us the possibility to know
            if we display the message or not
            - In create self is empty
            - In write self is not empty contains current ID
            :param values:
                - In create dictionary contains all recording
                    information self is False
                - In write we find only values changed
            :type values: dict
            :return: return dict object popup.message
                (self.env['popup.message'].read())
        """
        PopupMessage = self.env['popup.message']
        messages = PopupMessage.search([('model_id.model', '=', self._name)])
        if len(messages) > 0:
            object_popup = []

            for msg in messages:
                if any([item in msg.field_name for item in values]):
                    dict_popup = {
                        'model_id': msg.model_id,
                        'model': msg.model,
                        'field_ids': msg.field_ids,
                        'field_name': msg.field_name,
                        'popup_type': msg.popup_type,
                        'title': msg.title,
                        'message': msg.message,
                        'active': msg.active,
                    }
                    object_popup.append(dict_popup)
            return object_popup
        else:
            return False

    def execute_processing(self, values=False):
        """
            This function gives us the possibility to execute a
                specific treatment after the confirmation of the message
            - In create self is empty
            - In write self is not empty contains current ID
            :param values : a list of dictionaries:
                {'name': field, 'value': value of field}
            :type dictionary list
            :return boolean
        """
        return False
