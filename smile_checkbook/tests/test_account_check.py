# -*- coding: utf-8 -*-
# (C) 2018 Smile (<http://www.smile.fr>)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo.tests.common import TransactionCase


class TestAccountCheck(TransactionCase):

    def setUp(self):
        super(TestAccountCheck, self).setUp()
        self.check_manager = self.env['res.users'].create(
            {'name': 'Check Manager',
             'login': 'check_manager',
             'groups_id': [
                 (4, self.ref('base.group_system')),
                 (4, self.ref('smile_checkbook.group_account_check_manager')),
                 (4, self.ref('base.group_user'))]})
        self.check_user = self.env['res.users'].create(
            {'name': 'Check User',
             'login': 'check_user',
             'groups_id': [(4, self.ref('base.group_system')),
                           (4, self.ref('smile_checkbook.group_account_check_user'))]})
        self.env['account.check'].search([]).unlink()

    def _generate_checks(self):
        vals = {
            'partner_id': self.check_user.partner_id.id,
            'company_id': self.check_user.partner_id.company_id.id if self.check_user.partner_id.company_id else
            self.env.ref('base.main_company', raise_if_not_found=False).id,
            'quantity': 10,
            'from_number': 1802838,
        }
        wizard = self.env['account.checkbook.wizard'].with_user(
            self.check_manager).create(vals)
        self._run_onchange(wizard.with_user(self.check_manager))
        wizard.with_user(self.check_manager).generate_checks()
        return self.env['account.check'].search([]).sorted(key='number')

    def _run_onchange(self, wizard):
        wizard.onchange_range_of_numbers()
        wizard.onchange_to_number()

    def test_onchange_on_checkbook_wizard(self):
        """ As account manager, I open wizard to generate a checkbook.
        I choose 10 as quantity and 1802838 as start of range of numbers.
        I check that stop of range of numbers is computed as 1802848.
        I empty quantity and range of numbers.
        I choose 123638 to 123658 as start and stop of range of numbers.
        I check that quantity is computed as 20.
        """
        vals = {
            'partner_id': self.check_user.partner_id.id,
            'company_id': self.check_user.partner_id.company_id.id if self.check_user.partner_id.company_id else
            self.env.ref('base.main_company', raise_if_not_found=False).id,
            'quantity': 10,
            'from_number': 1802838,
        }
        wizard = self.env['account.checkbook.wizard'].with_user(
            self.check_manager).create(vals)
        self._run_onchange(wizard.with_user(self.check_manager))
        self.assertEquals(10, wizard.quantity)
        self.assertEquals(1802838, wizard.from_number)
        self.assertEquals(1802847, wizard.to_number)
        wizard.with_user(self.check_manager).write({
            'quantity': 0,
            'from_number': 0,
            'to_number': 0,
        })
        wizard.with_user(self.check_manager).write({
            'from_number': 123638,
            'to_number': 123657,
        })
        self._run_onchange(wizard.with_user(self.check_manager))
        self.assertEquals(20, wizard.quantity)
        self.assertEquals(123638, wizard.from_number)
        self.assertEquals(123657, wizard.to_number)

    def test_generate_checks(self):
        """ As account manager, I open wizard to generate a checkbook.
        I configure it to generate 10 checkbooks from 1802838.
        I check than 10 checks where generated.
        I check that their number covers the choosen range of numbers.
        I check that they are all available.
        """
        vals = {
            'partner_id': self.check_user.partner_id.id,
            'company_id': self.check_user.partner_id.company_id.id if self.check_user.partner_id.company_id else
            self.env.ref('base.main_company', raise_if_not_found=False).id,
            'quantity': 10,
            'from_number': 1802838,
        }
        wizard = self.env['account.checkbook.wizard'].with_user(
            self.check_manager).create(vals)
        self._run_onchange(wizard.with_user(self.check_manager))
        wizard.with_user(self.check_manager).generate_checks()
        checks = self.env['account.check'].search([]).sorted(key='number')
        self.assertEquals(10, len(checks))
        for index, check in enumerate(checks):
            self.assertEquals(1802838 + index, check.number)
            self.assertEquals('available', check.state)

    def test_update_state_of_check(self):
        """ As check user, I update state of one of my check to "Used".
        I check that the check is now used.
        I update state of another check to "Lost".
        I check that the check is now lost.
        """
        checks = self._generate_checks()
        check = checks[0]
        check.with_user(self.check_user).state = 'used'
        self.assertEquals('used', check.state)
        check = checks[5]
        check.with_user(self.check_user).state = 'lost'
        self.assertEquals('lost', check.state)
