# -*- encoding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2011 Smile (<http://www.smile.fr>). All Rights Reserved
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

from email.utils import COMMASPACE

from openerp import api, models, tools
from openerp.addons.base.ir.ir_mail_server import _logger, encode_rfc2822_address_header


class IrMailServer(models.Model):
    _inherit = "ir.mail_server"

    @api.model
    def send_email(self, message, mail_server_id=None, smtp_server=None, smtp_port=None,
                   smtp_user=None, smtp_password=None, smtp_encryption=None, smtp_debug=False):
        if not tools.config.get('enable_email_sending'):
            _logger.warning('Email sending not enabled')
            return False
        return super(IrMailServer, self).send_email(message, mail_server_id, smtp_server, smtp_port,
                                                    smtp_user, smtp_password, smtp_encryption, smtp_debug)

    def build_email(self, email_from, email_to, subject, body, email_cc=None, email_bcc=None, reply_to=False,
                    attachments=None, message_id=None, references=None, object_id=False, subtype='plain', headers=None,
                    body_alternative=None, subtype_alternative='plain'):
        msg = super(IrMailServer, self).build_email(email_from, email_to, subject, body, email_cc, email_bcc, reply_to,
                                                    attachments, message_id, references, object_id, subtype, headers,
                                                    body_alternative, subtype_alternative)
        if tools.config.get('email_to'):
            msg.replace_header('To', encode_rfc2822_address_header(COMMASPACE.join([tools.config['email_to']])))
            if 'Cc' in msg:
                msg.replace_header('Cc', None)
            if 'Bcc' in msg:
                msg.replace_header('Bcc', None)
        return msg
