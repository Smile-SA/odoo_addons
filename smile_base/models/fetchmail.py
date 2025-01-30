# -*- coding: utf-8 -*-
# (C) 2019 Smile (<http://www.smile.eu>)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import models, tools
import logging

_logger = logging.getLogger(__name__)


class FetchmailServer(models.Model):
    _inherit = "fetchmail.server"

    def fetch_mail(self):
        if not tools.config.get('enable_email_fetching'):
            _logger.warning('Email fetching not enabled')
            return False
        return super(FetchmailServer, self).fetch_mail()
