# -*- coding: utf-8 -*-
# (C) 2019 Smile (<http://www.smile.eu>)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import models, tools
from odoo.addons.mail.models import mail_template


class MailComposeMessage(models.TransientModel):
    _inherit = 'mail.compose.message'

    def prepare_and_send(self, model, partner_ids, template_id, res_id,
                         composition_mode='mass_mail'):
        """
        Prepare the message then send it.

        @param model: string, model name
        @param partner_ids: int list, ids of message receivers
        @param template_id: int, id of the email template
        @param res_id: int, id of the record from where the email is sent
        """
        def format_tz(dt, tz=False, format=False):
            return mail_template.format_tz(self._model, self._cr, self._uid,
                                           dt, tz, format, self._context)
        template = self.env['mail.template'].browse(template_id)
        # usefull to get template language
        ctx = {'mail_auto_delete': template.auto_delete,
               'mail_notify_user_signature': False,
               'tpl_partners_only': False}
        arg = {
            'object': self.env[model].browse(res_id),
            'user': self.env.user,
            'ctx': ctx,
            'format_tz': format_tz,
        }
        lang = mail_template.mako_template_env.from_string(
            tools.ustr(template.lang)).render(arg)

        message = self.with_context(active_ids=None).create({
            'model': model,
            'composition_mode': composition_mode,
            'partner_ids': [(6, 0, list(filter(None, partner_ids or [])))],
            'template_id': template_id,
            'notify': True,
            'res_id': res_id,
        })
        message_lang = message.with_context(lang=lang) \
            if lang and lang != 'False' else message
        value = message_lang.onchange_template_id(
            template_id, composition_mode, model, res_id)['value']
        if value.get('attachment_ids') and (
                composition_mode == 'comment' or not template.report_template):
            value['attachment_ids'] = [
                (4, attachment_id)
                for attachment_id in value['attachment_ids']]
        message.write(value)
        message.send_mail()
