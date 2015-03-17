# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2015 Smile (<http://www.smile.fr>). All Rights Reserved
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

from openerp import models


class MailComposeMessage(models.TransientModel):
    _inherit = 'mail.compose.message'

    def prepare_and_send(self, model, partner_ids, template_id, res_id, composition_mode='mass_mail'):
        """
        Prepare the message then send it.

        @param model: string, model name
        @param partner_ids: int list, ids of message receivers
        @param template_id: int, id of the email template
        @param res_id: int, id of the record from where the email is sent
        """
        message = self.with_context(active_ids=None).create({
            'model': model,
            'composition_mode': composition_mode,
            'partner_ids': [(6, 0, filter(None, partner_ids or []))],
            'template_id': template_id,
            'notify': True,
            'res_id': res_id,
        })
        value = message.onchange_template_id(template_id, composition_mode, model, res_id)['value']
        template = self.env['email.template'].browse(template_id)
        if value.get('attachment_ids') and (composition_mode == 'comment' or not template.report_template):
            value['attachment_ids'] = [(4, attachment_id) for attachment_id in value['attachment_ids']]
        message.write(value)
        message.send_mail()
