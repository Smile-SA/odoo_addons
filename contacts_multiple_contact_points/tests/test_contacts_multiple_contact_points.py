# (C) 2025 Smile (<http://www.smile.fr>)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo.tests import TransactionCase


class TestContactsMultipleContactPoints(TransactionCase):

    def setUp(self):
        super().setUp()
        self.ResPartner = self.env["res.partner"]

    def test_01_check_contact_point_is_created_for_phone(self):
        """
            Test that a contact point is created when a phone is provided.

            Prerequisites:
                - Create a partner with a phone number

            Test:
                - Call helper method to create partner and check contact point

            Expected:
                - Verify that a contact point is created with
                the correct type and value
        """
        self._create_and_test_contact_point(
            "phone", "phone", "0606704850"
        )

    def test_02_check_contact_point_is_created_for_email(self):
        """
            Test that a contact point is created when an email is provided.

            Prerequisites:
                - Create a partner with an email address

            Test:
                - Call helper method to create partner and check contact point

            Expected:
                - Verify that a contact point is created with
                the correct type and value
        """
        self._create_and_test_contact_point(
            "email", "email", "test@example.com"
        )

    def test_05_check_updates_on_phone_field_create_contact_points(self):
        """
            Test that updating the phone field creates contact points.

            Prerequisites:
                - Create a partner with an initial phone number

            Test:
                - Update the partner's phone number

            Expected:
                - Verify that a new contact point is created
                - Check that the default status is updated correctly
        """
        self._check_updates_create_contact_points(
            "phone", "0606704850", "0700112233"
        )

    def test_07_check_updates_on_email_field_create_contact_points(self):
        """
            Test that updating the email field creates contact points.

            Prerequisites:
                - Create a partner with an initial email address

            Test:
                - Update the partner's email address

            Expected:
                - Verify that a new contact point is created
                - Check that the default status is updated correctly
        """
        self._check_updates_create_contact_points(
            "email", "test1@example.com", "test2@example.com"
        )

    def test_08_check_unlink_contact_point(self):
        """
            Test that unlinking a contact point updates the partner field.

            Prerequisites:
                - Create a partner with a phone number
                - Update the phone number to create a second contact point

            Test:
                - Delete the latest contact point

            Expected:
                - Check that the phone field is cleared on the partner
        """
        test_partner = self.ResPartner.create({
            "name": "Test Partner",
            "phone": "0644505688",
        })
        test_partner.write(
            {"phone": "0644505050"}
        )
        last_created_contact_point = test_partner.contact_point_ids.sorted(
            'create_date'
        )[-1]
        last_created_contact_point.unlink()
        self.assertFalse(test_partner.phone)

    def test_09_check_update_on_contact_point(self):
        """
            Test that updating a contact point updates the partner field.

            Prerequisites:
                - Create a partner with a phone number

            Test:
                - Update the contact point's value

            Expected:
                - Check that the phone field on the partner
                is updated accordingly
        """
        test_partner = self.ResPartner.create(
            {
                "name": "Test Partner",
                "phone": "0644505688",
            }
        )
        test_partner.contact_point_ids.write(
            {
                "name": "0644444444"
            }
        )
        self.assertEqual(
            test_partner.phone,
            "0644444444",
            "Update on contact point should be reflected on contact also."
        )

    def _create_and_test_contact_point(
            self, contact_point_type, field_name, field_value
    ):
        test_partner = self.ResPartner.create({
            "name": "Test Partner",
            field_name: field_value,
        })
        # Check that contact points are created
        self.assertIsNotNone(
            test_partner.contact_point_ids,
            "The contact points should be created."
        )
        # Check that it's only one contact point is created
        # for the related partner
        self.assertEqual(
            1,
            len(test_partner.contact_point_ids),
            "There should be one contact point initially."
        )
        # Check that the tag is correctly associated with the created partner
        tag_contact_point_type = (
            test_partner.contact_point_ids.tag_id.contact_point_type
        )
        self.assertEqual(tag_contact_point_type, contact_point_type)
        # Check that the created contact point is default
        self.assertEqual(
            test_partner.contact_point_ids.is_default,
            True,
            "The created contact point should be marked as default."
        )
        """ Check that the name of the created contact point
            is equal to field_value """
        msg = (
            f"The name of the created contact point should be equal "
            f"to {field_value}"
        )
        self.assertEqual(
            test_partner.contact_point_ids.name,
            field_value,
            msg
        )

    def _check_updates_create_contact_points(
            self, field_name, initial_value, updated_value
    ):
        # Create a partner with an initial value for the field
        test_partner = self.ResPartner.create({
            "name": "Test Partner",
            field_name: initial_value,
        })
        # Verify that one contact point is created for the initial value
        msg1 = (
            f"One contact point should exist for the initial "
            f"{field_name} value."
        )
        self.assertEqual(
            len(test_partner.contact_point_ids),
            1,
            msg1
        )
        # Update the partner's field value
        test_partner.write({field_name: updated_value})
        msg2 = (
            f"The partner's {field_name} field should be changed to the "
            f"updated_value."
        )
        self.assertEqual(
            getattr(test_partner, field_name),
            updated_value,
            msg2
        )
        # Verify that two contact points exist after the update
        msg3 = (
            f"Two contact points should exist after updating the "
            f"{field_name} field."
        )
        self.assertEqual(
            len(test_partner.contact_point_ids),
            2,
            msg3
        )
        first_created_contact_point = test_partner.contact_point_ids.sorted(
            'create_date'
        )[0]
        # Check that the first created contact point is not default
        self.assertEqual(
            first_created_contact_point.is_default,
            False,
            "The first created contact point should not be marked as default."
        )
        last_created_contact_point = test_partner.contact_point_ids.sorted(
            'create_date'
        )[-1]
        # Check that the last created contact point is default
        self.assertEqual(
            last_created_contact_point.is_default,
            True,
            "The last created contact point should be marked as default."
        )
        """ Check that the name of the last created contact point
          is equal to updated_value """
        msg4 = (
            f"The name of the last created contact point should be equal "
            f"to {updated_value}"
        )
        self.assertEqual(
            last_created_contact_point.name,
            updated_value,
            msg4
        )
