# -*- encoding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2015 Smile (<http://www.smile.fr>). All Rights Reserved
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

from datetime import datetime
from openerp.exceptions import AccessError, except_orm
from openerp.tests.common import TransactionCase


class test_document_access(TransactionCase):

    def setUp(self):
        """
            Creation of:
            *Document type
            *Groups
            *Access rights
            *User profile
            *Users
        """

        super(test_document_access, self).setUp()
        self.user_obj = self.env['res.users']
        self.group_obj = self.env['res.groups']
        self.doc_obj = self.env['ir.attachment']
        self.doc_type_obj = self.env['ir.attachment.type']
        self.access_obj = self.env['ir.model.access']

        # Creation of a doc type
        self.new_doc_type = self.doc_type_obj.create({'name': 'New Doc Type'})

        # Creation of groups
        self.group_can_create = self.group_obj.create({'name': 'Group can create'})
        self.group_cannot_create = self.group_obj.create({'name': 'Group cannot create'})

        # Creation of access rights
        self.ir_model_access_test1 = self.env['ir.model.access'].create({
            'name': 'CanCreateAccess',
            'model_id': self.ref('base.model_ir_attachment'),
            'group_id': self.group_can_create.id,
            'perm_read': True,
            'perm_create': True,
            'perm_write': True,
            'perm_unlink': True
        })

        self.ir_model_access_test2 = self.env['ir.model.access'].create({
            'name': 'CannotCreateAccess',
            'model_id': self.ref('base.model_ir_attachment'),
            'group_id': self.group_cannot_create.id,
            'perm_read': True,
            'perm_create': False,
            'perm_write': False,
            'perm_unlink': False
        })

        self.ir_model_access_test3 = self.env['ir.model.access'].create({
            'name': 'CanCreateAccessDocumentDirectory',
            'model_id': self.ref('document.model_document_directory'),
            'group_id': self.group_can_create.id,
            'perm_read': True,
            'perm_create': True,
            'perm_write': True,
            'perm_unlink': True
        })

        # Creation of user profiles
        self.profile_user_can_create = self.user_obj.create({
            'name': 'Profile User Can Create',
            'login': 'PUCC',
            'user_profile':  True,
            'groups_id': [
                (4, self.group_can_create.id),
                (4, self.env.ref('base.group_document_user').id),
                (4, self.env.ref('base.group_system').id)
            ],
        })

        self.profile_user_cannot_create = self.user_obj.create({
            'name': 'Profile User Cannot Create',
            'login': 'PUCNC',
            'user_profile':  True,
            'groups_id': [(6, 0, self.group_cannot_create.ids)],
        })

        # Creation of users
        self.user_can_create = self.user_obj.create({
            'name': 'User Can create',
            'login': 'UCC',
            'user_profile': False,
            'user_profile_id': self.profile_user_can_create.id,
        })

        self.user_cannot_create = self.user_obj.create({
            'name': 'User Cannot create',
            'login': 'UCNC',
            'user_profile': False,
            'user_profile_id': self.profile_user_cannot_create.id,
        })

        self.date_today = datetime.now().date()
        self.doc_values = ({
            'name': 'Doc Test 1',
            'document_type_id': self.new_doc_type.id,
            'document_date': self.date_today,
            'expiry_date': self.date_today.replace(year=self.date_today.year + 3)
        })

        self.doc_values2 = ({
            'name': 'Doc Test 2',
            'document_type_id': self.new_doc_type.id,
            'document_date': self.date_today,
            'expiry_date': self.date_today.replace(year=self.date_today.year + 3)
        })

        self.doc_values3 = ({
            'name': 'Doc Test 3',
            'document_type_id': self.new_doc_type.id,
            'document_date': self.date_today,
            'expiry_date': self.date_today.replace(year=self.date_today.year + 3)
        })

        self.doc_3 = self.doc_obj.create(self.doc_values3)

    def test_create_document_acess(self):
        """
            We try to create a document with two different user with two different rights
            One with perm_create = True, the other one with perm_create = False
            The first one should be created while the second should fail
        """
        if self.ir_model_access_test1.perm_create:
            res_create_success = self.doc_obj.sudo(self.user_can_create).create(self.doc_values)
            self.assertTrue(res_create_success)

        if self.ir_model_access_test2.perm_write is False and self.ir_model_access_test2.perm_create is False:
            with self.assertRaises(AccessError):
                self.doc_obj.sudo(self.user_cannot_create).create(self.doc_values2)

    def test_write_document_access(self):
        """
            We try to create a document with two different user with two different rights
            One with perm_write = True, the other one with perm_write = False
            The first one should be created while the second should fail
        """
        if self.ir_model_access_test1.perm_write:
            self.assertTrue(self.doc_obj.browse(self.doc_3.id).sudo(self.user_can_create).write({'name': 'Doc 3 renamed success'}))

        with self.assertRaises(except_orm):
            self.doc_obj.browse(self.doc_3.id).sudo(self.user_cannot_create).write({'name': 'Doc 3 renamed fail'})
