# -*- coding: utf-8 -*-
# (C) 2019 Smile (<http://www.smile.fr>)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields, models


class MailMessage(models.Model):
    _inherit = 'mail.message'

    subject = fields.Char(data_mask="'message_' || id::text")
    body = fields.Html(data_mask="'message_' || id::text")
    record_name = fields.Char(data_mask="model || ',' || res_id::text")
    email_from = fields.Char(data_mask="NULL")
    reply_to = fields.Char(data_mask="NULL")
    message_id = fields.Char(data_mask="NULL")
