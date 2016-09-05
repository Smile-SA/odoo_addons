# -*- encoding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2011 Smile (<http://www.smile.fr>). All Rights Reserved
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

from odoo.tests.common import TransactionCase


class TestGroups(TransactionCase):

    def setUp(self):
        super(TestGroups, self).setUp()
        self.users_obj = self.env['res.users']
        self.groups_obj = self.env['res.groups']

        # Create groups
        self.group1, self.group2 = map(lambda index: self.groups_obj.create({'name': 'Group %d' % index}), range(1, 3))

        # Create a group to be completed
        self.group_completion = self.groups_obj.create({'name': 'Group to be completed'})

        # Create an ir.model.access
        self.ir_model_access_test = self.env['ir.model.access'].create({'name': 'GroupTestCompletion',
                                                                        'model_id': self.ref('base.model_ir_model'),
                                                                        'group_id': self.group_completion.id,
                                                                        'perm_read': True,
                                                                        'perm_create': True,
                                                                        'perm_write': True,
                                                                        'perm_unlink': True})

        # Create user profiles
        self.user_profile1 = self.users_obj.create({
            'name': 'Profile 1',
            'login': 'profile1',
            'is_user_profile': True,
            'groups_id': [(4, self.group1.id)],
        })
        self.user_profile2 = self.users_obj.create({
            'name': 'Profile 2',
            'login': 'profile2',
            'is_user_profile': True,
            'groups_id': [(6, 0, (self.group1 | self.group2).ids)],
        })
        # Create users
        self.user = self.users_obj.create({
            'name': 'Demo User',
            'login': 'demouser',
            'user_profile_id': self.user_profile2.id,
        })

    def test_write(self):
        """
            Test write method
        """
        self.assertTrue(self.group1.write({'name': 'Group 1 EDITED'}))
        self.assertEquals('Group 1 EDITED', self.group1.name)
        self.assertTrue((self.group1 | self.group2).write({'implied_ids': [(5,)]}))
        self.assertEquals(self.env['res.groups'].browse(), self.group1.implied_ids)
        self.assertEquals(self.env['res.groups'].browse(), self.group2.implied_ids)
        self.assertTrue((self.group1 | self.group2).write({'implied_ids': [(4, self.group_completion.id)]}))
        self.assertEquals(self.group_completion, self.group1.implied_ids)
        self.assertEquals(self.group_completion, self.group2.implied_ids)

    def test_button_complete_access_controls(self):
        """
            Test button_complete_access_controls method
            It tests _get_relation and _get_first_level_relation in the same time
            We use the group created in the setUp. It has only one object : object
            Clicking this button is supposed to add four objects
            We also check we got correct rights (True,False,False,False)
        """
        expected_list_after_completion = ['Models', 'ir.model.access', 'Fields', 'ir.ui.view', 'Users']
        list_after_completion = []
        check_right = True
        self.group_completion.button_complete_access_controls()
        for i in self.group_completion.model_access:
            list_after_completion.append(i.model_id.name)
            if i.model_id.name != "Models":
                if not i.perm_read or i.perm_write or i.perm_create or i.perm_unlink:
                    check_right = False
        for model in expected_list_after_completion:
            self.assertIn(model, list_after_completion, '%s should have been added!' % model)
        self.assertTrue(check_right)
