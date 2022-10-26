# -*- coding: utf-8 -*-
# (C) 2019 Smile (<https://www.smile.eu>)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields, models


class MailTracking(models.Model):
    _inherit = 'mail.tracking.value'

    old_value_integer = fields.Integer(data_mask="NULL")
    old_value_float = fields.Float(data_mask="NULL")
    old_value_monetary = fields.Float(data_mask="NULL")
    old_value_char = fields.Char(data_mask="NULL")
    old_value_text = fields.Text(data_mask="NULL")
    old_value_datetime = fields.Datetime(data_mask="NULL")

    new_value_integer = fields.Integer(data_mask="NULL")
    new_value_float = fields.Float(data_mask="NULL")
    new_value_monetary = fields.Float(data_mask="NULL")
    new_value_char = fields.Char(data_mask="NULL")
    new_value_text = fields.Text(data_mask="NULL")
    new_value_datetime = fields.Datetime(data_mask="NULL")
