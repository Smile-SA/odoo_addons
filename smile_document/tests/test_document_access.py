# -*- coding: utf-8 -*-
# (C) 2019 Smile (<http://www.smile.eu>)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).


from odoo import fields
from odoo.exceptions import AccessError
from odoo.tests.common import TransactionCase


class Testdocumentaccess(TransactionCase):

    def setUp(self):
        """
            Creation of:
            *Document type
            *Groups
            *Access rights
            *User profile
            *Users
        """

        super(Testdocumentaccess, self).setUp()
        self.user_obj = self.env['res.users']
        self.group_obj = self.env['res.groups']
        self.doc_obj = self.env['ir.attachment']
        self.doc_type_obj = self.env['ir.attachment.type']
        self.access_obj = self.env['ir.model.access']

        # Creation of a doc type
        self.new_doc_type = self.doc_type_obj.create(
            {'name': 'New Doc Type'})

        # Creation of groups
        self.group_can_create = self.group_obj.create(
            {'name': 'Group can create'})
        self.group_cannot_create = self.group_obj.create(
            {'name': 'Group cannot create'})

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

        # Creation of users
        self.user_can_create = self.user_obj.create({
            'name': 'User Can create',
            'login': 'UCC',
            'groups_id': [
                (4, self.group_can_create.id),
                (4, self.env.ref('base.group_system').id)
            ],
        })

        self.user_cannot_create = self.user_obj.create({
            'name': 'User Cannot create',
            'login': 'UCNC',
            'groups_id': [(6, 0, self.group_cannot_create.ids)],
        })

        self.date_today = fields.Datetime.now()
        self.doc_values = ({
            'name': 'Doc Test 1',
            'document_type_id': self.new_doc_type.id,
            'document_date': self.date_today,
            'expiry_date': self.date_today.replace(
                year=self.date_today.year + 3)
        })

        self.doc_values2 = ({
            'name': 'Doc Test 2',
            'document_type_id': self.new_doc_type.id,
            'document_date': self.date_today,
            'expiry_date': self.date_today.replace(
                year=self.date_today.year + 3)
        })

        self.doc_values3 = ({
            'name': 'Doc Test 3',
            'document_type_id': self.new_doc_type.id,
            'document_date': self.date_today,
            'expiry_date': self.date_today.replace(
                year=self.date_today.year + 3)
        })

        self.doc_3 = self.doc_obj.create(self.doc_values3)

    def test_create_document_acess(self):
        """ We try to create a document with two different user
            with two different rights.
        One with perm_create = True, the other one with perm_create = False.
        The first one should be created while the second should fail.
        """
        if self.ir_model_access_test1.perm_create:
            res_create_success = self.doc_obj.with_user(
                self.user_can_create).create(self.doc_values)
            self.assertTrue(res_create_success)

        if self.ir_model_access_test2.perm_write is False and \
                self.ir_model_access_test2.perm_create is False:
            with self.assertRaises(AccessError):
                self.doc_obj.with_user(self.user_cannot_create).create(
                    self.doc_values2)

    def test_write_document_access(self):
        """ We try to create a document with two different user
            with two different rights.
        One with perm_write = True, the other one with perm_write = False.
        The first one should be created while the second should fail.
        """
        if self.ir_model_access_test1.perm_write:
            self.assertTrue(self.doc_obj.browse(self.doc_3.id).with_user(
                self.user_can_create).write({'name': 'Doc 3 renamed success'}))

        with self.assertRaises(AccessError):
            self.doc_obj.browse(self.doc_3.id).with_user(
                self.user_cannot_create).write({'name': 'Doc 3 renamed fail'})
