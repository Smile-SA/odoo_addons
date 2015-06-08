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

from openerp import api, models, tools
from openerp.addons.mail.mail_mail import _logger


class MailMail(models.Model):
    _inherit = 'mail.mail'

    @api.cr_uid
    def process_email_queue(self, cr, uid, ids=None, context=None):
        if not tools.config.get('enable_email_sending'):
            _logger.warning('Email sending not enable')
            return True
        return super(MailMail, self).process_email_queue(cr, uid, ids, context)
