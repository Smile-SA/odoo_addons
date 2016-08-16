# -*- encoding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2013 Smile (<http://www.smile.fr>). All Rights Reserved
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

from contextlib import contextmanager

from openerp.tests.common import TransactionCase
from openerp.tools.config import config
from openerp.addons.base.ir.ir_mail_server import MailDeliveryException


@contextmanager
def config_to_enable_email_sending(enable_email_sending):
    init_config = {
        'enable_email_sending': config.get('enable_email_sending'),
    }
    try:
        config['enable_email_sending'] = enable_email_sending
        yield config
    finally:
        for key, value in init_config.iteritems():
            config[key] = value


class BaseTest(TransactionCase):

    def setUp(self):
        super(BaseTest, self).setUp()
        self.model = self.env['res.partner.category']

    def test_bulk_create(self):
        """
            I create three categories with the same method call
            I check that three categories were created
        """
        names = ['t1', 't2', 't3']
        vals_list = [{'name': name} for name in names]
        categories = self.model.bulk_create(vals_list)
        self.assertEquals(3, len(categories), 'Three categories shoudl have been created!')
        self.assertListEqual(names, sorted(categories.mapped('name')),
                             'Names of the created categories are wrong!')

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
            self.assertEquals('exception', email.state, 'Email should be in exception!')

    def test_enable_email_sending(self):
        """
            I enable email sending in config file
            I send an email
            I check that email was sent
        """
        # I remove all outgoing mail server to be sure the exception will be raised
        self.env['ir.mail_server'].search([]).unlink()
        email = self._get_email()
        with config_to_enable_email_sending(True):
            with self.assertRaises(MailDeliveryException):
                email.send(raise_exception=True)
