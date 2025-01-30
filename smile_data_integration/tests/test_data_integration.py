# -*- coding: utf-8 -*-
# (C) 2020 Smile (<https://www.smile.eu>)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

import time

from odoo.exceptions import UserError
from odoo.service.model import execute_kw
from odoo.tests.common import TransactionCase


class DataIntegrationTest(TransactionCase):

    def setUp(self):
        super(DataIntegrationTest, self).setUp()
        self.xml_id = 'base.res_partner_3'

    def call_service(self, model, method, *args, **kwargs):
        db = self.env.cr.dbname
        uid = self.env.user.id
        return execute_kw(db, uid, model, method, args, kwargs)

    def get_partner_country_id(self, partner_id):
        res = self.call_service(
            'res.partner', 'read', partner_id, ['country_id'])
        return res[0]['country_id'][0]

    def test_10_create_with_xml_id_in_vals(self):
        xml_id = 'base.fr'
        vals = {'name': 'Test', 'country_id': xml_id}
        partner_id = self.call_service('res.partner', 'create', vals)
        country_id = self.get_partner_country_id(partner_id)
        self.assertEqual(country_id, self.ref(xml_id))

    def test_20_write_with_xml_id_in_vals(self):
        xml_id = 'base.be'
        vals = {'country_id': xml_id}
        res = self.call_service('res.partner', 'write',
                                self.ref(self.xml_id), vals)
        self.assertTrue(res)
        country_id = self.get_partner_country_id(self.ref(self.xml_id))
        self.assertEqual(country_id, self.ref(xml_id))

    def test_30_write_with_xml_id_in_ids(self):
        xml_id = 'base.de'
        vals = {'country_id': self.ref(xml_id)}
        res = self.call_service('res.partner', 'write', self.xml_id, vals)
        self.assertTrue(res)
        country_id = self.get_partner_country_id(self.ref(self.xml_id))
        self.assertEqual(country_id, self.ref(xml_id))

    def test_40_search_with_xml_id_in_domain(self):
        xml_id = 'base.us'
        domain = [('country_id', '=', xml_id)]
        count = self.call_service('res.partner', 'search_count', domain)
        self.assertTrue(count)
        res = self.call_service('res.partner', 'search_read',
                                domain, ['country_id'])
        self.assertEqual(res[0]['country_id'][0], self.env.ref(xml_id).id)
        ids = self.call_service('res.partner', 'search', domain)
        self.assertTrue(ids)
        country_id = self.get_partner_country_id(ids[0])
        self.assertEqual(country_id, self.ref(xml_id))

    def test_50_user_context(self):
        domain = [('id', '=', self.ref(self.xml_id))]
        self.call_service(
            'res.partner', 'write', self.xml_id, {'active': False})
        self.call_service(
            'res.users', 'write', self.env.uid, {'context_active_test': True})
        context = self.call_service('res.users', 'context_get')
        ids = self.call_service(
            'res.partner', 'search', domain, 0, 0, "", context)
        self.assertFalse(ids)
        self.call_service(
            'res.users', 'write', self.env.uid, {'context_active_test': False})
        context = self.call_service('res.users', 'context_get')
        ids = self.call_service(
            'res.partner', 'search', domain, 0, 0, "", context)
        self.assertTrue(ids)
        self.call_service(
            'res.users', 'write', self.env.uid, {'context_active_test': True})

    def test_60_load_with_inactive_xml_id(self):
        self.call_service('res.partner', 'write', self.ref(self.xml_id), {
            'active': False,
        })
        self.call_service('res.users', 'write', self.env.uid, {
            'context_active_test': False,
            'context_raise_load_exceptions': True,
        })
        context = self.call_service('res.users', 'context_get')
        fields = ['acc_number', 'acc_type', 'partner_id__id']
        data = [[time.strftime("%Y%m%d%H%M%S"), 'bank', self.xml_id]]
        res = self.call_service(
            'res.partner.bank', 'load', fields, data, context)
        self.assertTrue(res['ids'])
        self.assertFalse(res['messages'])
        with self.assertRaises(UserError):
            self.call_service(
                'res.partner.bank', 'load', fields, data, context)

    def test_70_unlink_with_xml_id_in_ids(self):
        xml_id = 'smile_data_integration.test'
        model = 'res.partner.bank'
        fields = ['id', 'acc_number', 'acc_type', 'partner_id__id']
        data = [[xml_id, time.strftime("%Y%m%d%H%M%SX"), 'bank', self.xml_id]]
        context = self.call_service('res.users', 'context_get')
        res = self.call_service(model, 'load', fields, data, context)
        self.assertTrue(res['ids'])
        self.call_service(model, 'unlink', xml_id)
        self.assertFalse(self.call_service(model, 'exists', res['ids']))
