# -*- coding: utf-8 -*-
# (C) 2018 Smile (<http://www.smile.fr>)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo.tests.common import TransactionCase


class FilteredFromDomainTest(TransactionCase):

    def test_filtered_from_domain(self):
        Partner = self.env['res.partner']
        domain = [('is_company', '=', True)]
        self.assertEquals(
            Partner.search([]).filtered_from_domain(domain),
            Partner.search(domain))
