# -*- coding: utf-8 -*-
# (C) 2011 Smile (<http://www.smile.fr>)
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl).

from odoo.tests.common import TransactionCase
from odoo.exceptions import ValidationError


class TestUsers(TransactionCase):

    def setUp(self):
        super(TestUsers, self).setUp()
        Users = self.env['res.users']
        Groups = self.env['res.groups']

        # Create groups
        self.group1, self.group2 = map(
            lambda index: Groups.create(
                {'name': 'Group %d' % index}), range(1, 3))

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
        userEdited = self.env['res.users'].browse(
            self.user.id).write({'user_profile_id': self.user_profile2.id})
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
            self.env['res.users'].browse(
                self.user.id).write({'user_profile_id': admin})
