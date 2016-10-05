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
from odoo.exceptions import ValidationError


class TestAccessControl(TransactionCase):

    def setUp(self):
        super(TestAccessControl, self).setUp()
        Users = self.env['res.users']
        Groups = self.env['res.groups']
        # Create groups
        self.group1, self.group2 = map(lambda index: Groups.create({'name': 'Group %d' % index}), range(1, 3))
        # Create user profiles
        self.user_profile1 = Users.create({
            'name': 'Profile 1',
            'login': 'profile1',
            'is_user_profile': True,
            'groups_id': [(4, self.group1.id)],
        })
        self.user_profile2 = Users.create({
            'name': 'Profile 2',
            'login': 'profile2',
            'is_user_profile': True,
            'groups_id': [(6, 0, (self.group1 | self.group2).ids)],
        })
        # Create users
        self.user = Users.create({
            'name': 'Demo User',
            'login': 'demouser',
            'user_profile_id': self.user_profile1.id,
        })

    def test_changing_a_group_dependencies_should_update_groups_of_user_belonging_to_this_group(self):
        """
            Add Group 1 to Demo User dependencies.
            Add a dependence to Group 2 to the group Group 1.
            Check that user has this new dependence.
        """
        self.group1.implied_ids = [(4, self.group2.id)]
        self.assertIn(self.group2, self.user.groups_id, 'The user has not the new dependence!')

    def test_changing_user_profile_of_a_user_should_update_groups_of_user(self):
        """
            Add Group 2 to the dependencies of Group 1.
            Check that user has this new dependence.
        """
        self.user.user_profile_id = self.user_profile2
        for group in self.user_profile2.groups_id:
            self.assertIn(group, self.user.groups_id, 'The user has not the new dependence!')

    def test_change_profile_with_no_update_users_do_not_change_users(self):
        """
            Change Profile 2 to not update users
            Remove Group 1 in Profile 2.
            Check that user has again Group 1.
        """
        self.user.user_profile_id.is_update_users = False
        self.assertIn(self.group1, self.user.groups_id, 'The user has not the Group 1 in dependencies !')

    def test_using_admin_as_profile_should_fail(self):
        """
            I try to create a user with Administrator as user profile
            I check that it failed
        """
        with self.assertRaisesRegexp(ValidationError, "You can't use (.*) as user profile !"):
            self.env['res.users'].create({
                'name': 'toto',
                'login': 'toto',
                'user_profile_id': self.env.ref('base.user_root').id
            })

    def test_update_users_of_a_group(self):
        """
            I create a user U and a profile P
            I update group Group 1 to add it user U
            I check that
        """
        profile = self.env['res.users'].create({'name': 'P', 'login': 'p_login', 'is_user_profile': True})
        user = self.env['res.users'].create({'name': 'U', 'login': 'u_login', 'user_profile_id': profile.id})
        self.group1.with_context(use_pdb=True).users |= profile
        self.assertIn(self.group1, user.groups_id, 'User U should have Group 1 in dependencies!')
