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

from openerp.tests.common import TransactionCase


class TestGroup(TransactionCase):

    def test_update_user_group(self):
        """
            Create a group and an user.
            Assign this group to the user.
            Add a dependence to the group.
            Check that user has this new dependence.
        """
        user = self.env['res.users'].create({'name': 'Me', 'login': 'me'})
        group = self.env['res.groups'].create({'name': 'Test Group', 'users': [(6, 0, [user.id])]})
        self.assertEquals(user.id, group.users.id, 'User was not added to the group !')
        new_group = self.env['res.groups'].create({'name': 'Test Group 2'})
        group.implied_ids = [(4, new_group.id)]
        self.assertIn(new_group, user.groups_id, 'The user has not the new dependence !')
