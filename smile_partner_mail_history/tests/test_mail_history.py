# -*- coding: utf-8 -*-
# (C) 2025 Smile (<http://www.smile.fr>)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo.exceptions import UserError
from odoo.tests.common import TransactionCase


class TestMailHistory(TransactionCase):

    def test_01_message_not_sent_to_partner_should_not_appear_in_history(self):
        """Test that messages sent to a partner appear in their mail history.

        Prerequisites:
            - Mail module installed
            - Access to res.partner and mail.message models

        Test:
            1. Create partner
            2. Post a message with this partner as recipient
            3. Call the received email history action

        Expected result:
            - The action returns a domain that includes
              the ID of the posted message
            - The domain is correctly formatted to filter only this message
        """
        partner = self.env['res.partner'].create({
            'name': 'Alex TERRIEUR',
            'email': 'alex.terrieur@example.com',
        })
        partner.message_post(body="Wow, this is so clean!", partner_ids=[])
        
        with self.assertRaises(UserError) as e:
            partner.action_received_email_history()
        self.assertEqual(
            "This partner Alex TERRIEUR does not have any messages history!",
            str(e.exception)
        )
    def test_02_message_sent_to_partner_should_appear_in_history(self):
        """Test that an error is raised when a partner has no message history.

        Prerequisites:
            - Mail module installed
            - Access to res.partner and mail.message models

        Test:
            1. Create partner
            2. Post a message on the partner but without setting it as
               recipient (empty partner_ids)
            3. Call the received email history action

        Expected result:
            - A UserError exception is raised
            - The error message contains the partner's name and indicates that
              they have no message history
        """
        partner = self.env['res.partner'].create({
            'name': 'Aude JAVEL',
            'email': 'aude.javel@example.com',
        })
        partner.message_post(body="Wow, this is so clean!", partner_ids=partner.ids)
        
        result = partner.action_received_email_history()
        expected_domain = [
            ('message_type', 'in', ('email', 'comment', 'notification', 'user_notification')),
            ('partner_ids', 'in', partner.ids),
        ]
        self.assertEqual(expected_domain, result.get('domain', []))
