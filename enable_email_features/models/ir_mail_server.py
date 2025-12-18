from odoo import api, models, tools
from odoo.addons.base.models.ir_mail_server import _logger


class IrMailServer(models.Model):
    _inherit = "ir.mail_server"

    @api.model
    def send_email(self, message, mail_server_id=None, smtp_server=None,
                   smtp_port=None, smtp_user=None, smtp_password=None,
                   smtp_encryption=None, smtp_debug=False, smtp_session=None):
        if not tools.config.get('enable_email_sending'):
            _logger.warning('Email sending not enabled')
            return False
        return super(IrMailServer, self).send_email(
            message, mail_server_id, smtp_server, smtp_port, smtp_user,
            smtp_password, smtp_encryption, smtp_debug, smtp_session)
