# -*- coding: utf-8 -*-
# (C) 2019 Smile (<http://www.smile.eu>)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo.tests.common import TransactionCase


class TestAnonymization(TransactionCase):

    def setUp(self):
        super().setUp()
        user_vals = {
            'name': 'Test',
            'login': 'test',
            'groups_id': [
                (4, self.env.ref('base.group_user').id),
                (4, self.env.ref(
                    'smile_anonymize_partner.group_anonymize_partner').id),
            ],
        }
        self.user = self.env['res.users'].create(user_vals)

    def test_anonymization_on_enabled_partner(self):
        partner_vals = {
            'name': 'Toto',
            'street': '123 dummy street',
            'city': 'Paris',
            'phone': '+33102030405',
            'email': 'test@example.com',
        }
        partner = self.env['res.partner'].create(partner_vals)
        context = partner.sudo(
            self.user).action_anonymization()['context']
        anonymize_partner_wizard = \
            self.env['confirm.anonymization'].with_context(
                active_ids=context.get('active_ids')).create({})
        anonymize_partner_wizard.sudo(self.user).action_confirm()
        self.assertTrue(partner.is_anonymized)
        self.assertFalse(partner.active)
        self.assertEquals("name%d-anonym" % partner.id, partner.name)
        self.assertEquals("name%d-anonym" % partner.id, partner.display_name)
        self.assertEquals("street%d-anonym" % partner.id, partner.street)
        self.assertEquals("Paris", partner.city)
        self.assertEquals("+33000000000", partner.phone)
        self.assertEquals(
            "email%d-anonymise@anonymise.fr" % partner.id, partner.email)

    def test_anonymization_on_disabled_partner(self):
        partner_vals = {
            'name': 'Toto',
            'street': '123 dummy street',
            'city': 'Paris',
            'phone': '+33102030405',
            'email': 'test@example.com',
        }
        partner = self.env['res.partner'].create(partner_vals)
        partner.toggle_active()
        self.assertFalse(partner.active)
        context = partner.sudo(
            self.user).action_anonymization()['context']
        anonymize_partner_wizard = \
            self.env['confirm.anonymization'].with_context(
                active_ids=context.get('active_ids')).create({})
        anonymize_partner_wizard.sudo(self.user).action_confirm()
        self.assertTrue(partner.is_anonymized)
        self.assertFalse(partner.active)
        self.assertEquals("name%d-anonym" % partner.id, partner.name)
        self.assertEquals("name%d-anonym" % partner.id, partner.display_name)
        self.assertEquals("street%d-anonym" % partner.id, partner.street)
        self.assertEquals("Paris", partner.city)
        self.assertEquals("+33000000000", partner.phone)
        self.assertEquals(
            "email%d-anonymise@anonymise.fr" % partner.id, partner.email)
