# -*- coding: utf-8 -*-
# (C) 2019 Smile (<http://www.smile.eu>)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from contextlib import contextmanager

from odoo.tests.common import TransactionCase
from odoo.tools.config import config
from odoo.addons.base.models.ir_mail_server import MailDeliveryException
from unittest.mock import patch


@contextmanager
def config_to_enable_email_sending(enable_email_sending):
    init_config = {
        'enable_email_sending': config.get('enable_email_sending'),
        'test_enable': config.get('test_enable'),
    }
    try:
        config['enable_email_sending'] = enable_email_sending
        config['test_enable'] = not enable_email_sending
        yield config
    finally:
        for key, value in init_config.items():
            config[key] = value


class BaseTest(TransactionCase):
    def setUp(self):
        super(BaseTest, self).setUp()
        self.model = self.env['res.partner.category']

    def test_unlink_cascade(self):
        parent = self.model.create({'name': 'Parent'})
        child = self.model.create({'name': 'Child', 'parent_id': parent.id})
        self.assertTrue(parent.unlink())
        self.assertFalse(child.exists())

    def _get_email(self):
        vals = {
            'subject': 'The subject',
            'body': 'and the body',
            'email_from': 'admin@example.org',
            'email_to': 'demo@example.org',
        }
        return self.env['mail.mail'].create(vals)

    def test_disable_email_sending(self):
        """
            I disable email sending in config file
            I send an email
            I check that no email was sent
        """
        email = self._get_email()
        with config_to_enable_email_sending(False):
            email.send()
            self.assertEqual('exception', email.state, 'Email should be in exception!')

    def test_enable_email_sending(self):
        """
            I enable email sending in config file
            I send an email
            I check that email was sent
        """
        # I remove all outgoing mail server to be sure
        # the exception will be raised
        self.env['ir.mail_server'].search([]).unlink()
        email = self._get_email()
        ir_mail_server = self.env['ir.mail_server']
        with patch.object(type(ir_mail_server), '_is_test_mode', lambda self: False):
            with config_to_enable_email_sending(True):
                with self.assertRaises(MailDeliveryException):
                    email.send(raise_exception=True)
