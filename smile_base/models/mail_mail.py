# -*- coding: utf-8 -*-
# (C) 2019 Smile (<http://www.smile.eu>)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import api, models, tools
from odoo.addons.mail.models.mail_mail import _logger


class MailMail(models.Model):
    _inherit = 'mail.mail'

    @api.model
    def process_email_queue(self, ids=None):
        if not tools.config.get('enable_email_sending'):
            _logger.warning('Email sending not enabled')
            return True
        return super(MailMail, self).process_email_queue(ids)
