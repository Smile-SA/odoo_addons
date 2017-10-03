# -*- coding: utf-8 -*-

from odoo import api, models


class MailComposeMessage(models.TransientModel):
    _inherit = 'mail.compose.message'

    @api.multi
    def send_mail(self, auto_commit=False):
        if self._context.get('default_model') == 'discount.contract' and \
                self._context.get('default_res_id') and self._context.get('mark_so_as_sent'):
            contract = self.env['discount.contract'].browse([self._context['default_res_id']])
            if contract.state == 'draft':
                contract.state = 'sent'
            self = self.with_context(mail_post_autofollow=True)
        return super(MailComposeMessage, self).send_mail(auto_commit=auto_commit)
