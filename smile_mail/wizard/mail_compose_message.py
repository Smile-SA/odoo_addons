# -*- coding: utf-8 -*-

from odoo import fields, models


class MailComposer(models.TransientModel):
    _inherit = 'mail.compose.message'

    body = fields.Html(default='<div></div>')
