# -*- coding: utf-8 -*-
# (C) 2019 Smile (<http://www.smile.fr>)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from openerp import fields, models


class MailTracking(models.Model):
    _inherit = 'mail.tracking.value'

    old_value_integer = fields.Integer(data_mask="NULL")
    old_value_float = fields.Float('Old Value Float', readonly=1, data_mask="NULL")
    old_value_monetary = fields.Float('Old Value Monetary', readonly=1, data_mask="NULL")
    old_value_char = fields.Char('Old Value Char', readonly=1, data_mask="'old_value_' || id::text")
    old_value_text = fields.Text('Old Value Text', readonly=1, data_mask="NULL")
    old_value_datetime = fields.Datetime('Old Value DateTime', readonly=1, data_mask="NULL")

    new_value_integer = fields.Integer(data_mask="NULL")
    new_value_float = fields.Float('New Value Float', readonly=1, data_mask="NULL")
    new_value_monetary = fields.Float('New Value Monetary', readonly=1, data_mask="NULL")
    new_value_char = fields.Char('New Value Char', readonly=1, data_mask="'new_value_' || id::text")
    new_value_text = fields.Text('New Value Text', readonly=1, data_mask="NULL")
    new_value_datetime = fields.Datetime('New Value Datetime', readonly=1, data_mask="NULL")



