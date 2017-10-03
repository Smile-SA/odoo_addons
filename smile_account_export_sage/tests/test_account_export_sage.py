# -*- coding: utf-8 -*-

from odoo.tests.common import TransactionCase


class AccountExportSageTest(TransactionCase):
    """
        Test account export to Sage
    """

    def setUp(self):
        super(AccountExportSageTest, self).setUp()
        accountant_group = self.env.ref('account.group_account_user')
        self.accountant = self.env['res.users'].search([
            ('groups_id', 'in', accountant_group.id)
        ], limit=1)
        if not self.accountant:
            self.accountant = self.env['res.users'].create({
                'name': 'Accountant User',
                'login': 'accountant',
                'groups_id': [(6, 0, [accountant_group.id])],
            })

    def test_010_create_payer(self):
        """
            1. As accountant, I create an export
            2. I un export
            3. I check if export is done
        """
        export = self.env['account.export'].create({
            'name': 'My export test',
            'provider': 'sage',
        })
        self.assertEquals(export.state, 'draft')
        export.run_export()
        self.assertEquals(export.state, 'done')
