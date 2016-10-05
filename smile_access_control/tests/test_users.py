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


class TestUsers(TransactionCase):

    def setUp(self):
        super(TestUsers, self).setUp()
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

    def test_create(self):
        """
            Test create method
            We create a dictionary of values
            We create a user from these values, he has a user profile
            We check that that the new user has been created with his name
        """
        userValue = {'name': 'User Test 1',
                     'login': 'usertest1',
                     'user_profile_id': self.user_profile2.id,
                     }
        Users = self.env['res.users']
        user_test = Users.create(userValue)
        newUser = self.env['res.users'].browse(user_test.id)
        self.assertEqual(userValue['name'], newUser['name'])

    def test_write(self):
        """
            Test write method
            We use the user created in the first method
            We change his user_profile_id
            We check if the update has been done
        """
        userEdited = self.env['res.users'].browse(self.user.id).write({'user_profile_id': self.user_profile2.id})
        self.assertEqual(userEdited, True)

    def test_check_user_profile_id(self):
        """
            Test _check_user_profile_id method
            We try to create a user with admin as user profile
            It raises a Validation Error
        """
        userValue = {'name': 'User Test 1',
                     'login': 'usertest1',
                     'user_profile_id': self.env.ref('base.user_root').id,
                     }
        with self.assertRaises(ValidationError):
            self.env['res.users'].create(userValue)

    def test_onchange_user_profile(self):
        """
            Test onchange user profile method
            We try to set the profile of an existing user to admin
            It raises a Validation Error
        """
        admin = self.env.ref('base.user_root').id
        with self.assertRaises(ValidationError):
            self.env['res.users'].browse(self.user.id).write({'user_profile_id': admin})
