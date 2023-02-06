# (C) 2023 Smile (<https://www.smile.eu>)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

import logging
from datetime import datetime

import pytz

from odoo import fields, api, models, _

_logger = logging.getLogger(__name__)


class IrCron(models.Model):
    _inherit = 'ir.cron'

    enable_history = fields.Boolean()

    @api.model
    def _callback(self, cron_name, server_action_id, job_id):
        cron = self.env['ir.cron'].sudo().browse(job_id)
        cron_history = False
        if cron.enable_history:
            cron_history = self.env['ir.cron.history']._create_history(
                cron_name, server_action_id)
            self = self.with_context(cron_history_id=cron_history.id)
        super(IrCron, self)._callback(cron_name, server_action_id, job_id)
        if cron_history:
            cron_history._done_history()

    @api.model
    def _trigger_alert(self, job_id, job_exception):
        if self.env.user.company_id.alert_failure_email:
            template = self.env.ref(
                'smile_cron_history.cron_failure_alert_mail_template',
                raise_if_not_found=True)
            active_tz = pytz.timezone(self.env.user.tz or 'UTC')
            return template.with_context({
                'date': datetime.now().replace(
                    tzinfo=pytz.utc).astimezone(active_tz).strftime('%H:%M'),
                'exception': job_exception.name
                if hasattr(job_exception, 'name') else job_exception
            }).send_mail(job_id, force_send=True)
        else:
            _logger.warning(
                _('No email configured to send Cron failure alert.'))

    @api.model
    def _handle_callback_exception(
            self, cron_name, server_action_id, job_id, job_exception):
        """Alert users by sending an email when a cron fails"""
        super(IrCron, self)._handle_callback_exception(
            cron_name, server_action_id, job_id, job_exception)
        self.env['ir.cron.history']._error_history(job_exception)
        self._trigger_alert(job_id, job_exception)
