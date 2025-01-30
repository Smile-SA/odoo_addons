# -*- coding: utf-8 -*-
# (C) 2020 Smile (<http://www.smile.fr>)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo.exceptions import UserError
from odoo.tests.common import TransactionCase


class TestMailHistory(TransactionCase):

    def test_message_sent_to_partner_should_appear_in_history(self):
        partner = self.env['res.partner'].create({
            'name': 'Aude JAVEL',
            'email': 'aude.javel@example.com',
        })
        message = partner.message_post(body="Wow, this is so clean!",
                                       partner_ids=partner.ids)
        result = partner.action_received_email_history()
        expected_domain = [('id', 'in', message.ids)]
        self.assertEquals(expected_domain, result.get('domain', []))

    def test_message_sent_on_partner_should_not_appear_in_history(self):
        partner = self.env['res.partner'].create({
            'name': 'Alex TERRIEUR',
            'email': 'alex.terrieur@example.com',
        })
        partner.message_post(body="Wow, this is so clean!",
                             partner_ids=[])
        with self.assertRaisesRegexp(
                UserError,
                "This partner Alex TERRIEUR does not "
                "have any messages history!"):
            partner.action_received_email_history()
