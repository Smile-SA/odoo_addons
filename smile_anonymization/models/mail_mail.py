# -*- coding: utf-8 -*-
# (C) 2019 Smile (<http://www.smile.fr>)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields, models


class MailMail(models.Model):
    _inherit = 'mail.mail'

    body_html = fields.Text(data_mask="'mail_' || id::text")
    email_to = fields.Text(data_mask="NULL")
    email_cc = fields.Char(data_mask="NULL")
