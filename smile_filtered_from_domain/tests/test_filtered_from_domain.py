# -*- coding: utf-8 -*-

from odoo.tests.common import TransactionCase


class FilteredFromDomainTest(TransactionCase):

    def test_filtered_from_domain(self):
        Partner = self.env['res.partner']
        domain = [('is_company', '=', True)]
        self.assertEquals(
            Partner.search([]).filtered_from_domain(domain),
            Partner.search(domain))
