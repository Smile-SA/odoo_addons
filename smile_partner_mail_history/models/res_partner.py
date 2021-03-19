# -*- coding: utf-8 -*-
# (C) 2020 Smile (<http://www.smile.fr>)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).


from odoo import fields, models, _
from odoo.exceptions import UserError

MAIL_MESSAGE_TYPES = ('email', 'comment', 'notification', 'user_notification')


class ResPartner(models.Model):
    _inherit = 'res.partner'

    messages_count = fields.Integer(compute='_compute_messages_count')

    def _compute_messages_count(self):
        Message = self.env['mail.message']
        for partner in self:
            partner.messages_count = Message.search_count([
                ('message_type', 'in', MAIL_MESSAGE_TYPES),
                ('partner_ids', 'in', partner.id),
            ])

    def action_received_email_history(self):
        """
        Show all received mail.message for a specific partner
        """
        self.ensure_one()
        Message = self.env['mail.message']
        # Get messages sent to this partner
        messages = Message.search([
            ('message_type', 'in', MAIL_MESSAGE_TYPES),
            ('partner_ids', 'in', self.id),
        ])
        if not messages:
            raise UserError(
                _('This partner %s does not have any messages history!')
                % self.display_name)
        # Build action to display all messages sent to this partner
        action = self.env.ref('mail.action_view_mail_message')
        result = action.read()[0]
        result['views'] = [
            (self.env.ref(
                'smile_partner_mail_history.'
                'view_message_tree_partner_mail_history').id,
                'tree'),
            (self.env.ref(
                'smile_partner_mail_history.'
                'view_message_form_partner_mail_history').id,
                'form'),
        ]
        result['domain'] = [('id', 'in', messages.ids)]
        return result
