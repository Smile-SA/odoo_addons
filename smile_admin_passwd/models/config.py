# -*- coding: utf-8 -*-
# (C) 2022 Smile (<https://www.smile.eu>)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

import odoo
from odoo.tools.config import configmanager, crypt_context

native_set_admin_password = configmanager.set_admin_password
native_verify_admin_password = configmanager.verify_admin_password


def new_set_admin_password(self, new_password):
    hash_password = crypt_context.hash if hasattr(
        crypt_context, 'hash') else crypt_context.encrypt
    new_hash_password = hash_password(new_password)
    # Added by Smile to save hash_password in database
    db_name = self.options.get('db_name')
    if db_name:
        with odoo.api.Environment.manage():
            with odoo.registry(db_name).cursor() as cr:
                env = odoo.api.Environment(cr, odoo.SUPERUSER_ID, {})
                env['admin.passwd'].create_or_set_passwd(new_hash_password)
    else:
        native_set_admin_password(self, new_password)


def new_verify_admin_password(self, password):
    db_name = self.options.get('db_name')
    if db_name:
        with odoo.api.Environment.manage():
            with odoo.registry(db_name).cursor() as cr:
                env = odoo.api.Environment(cr, odoo.SUPERUSER_ID, {})
                # Added by Smile retrieve from database
                stored_hash = \
                    env['admin.passwd'].get_passwd() or \
                    self.options['admin_passwd']
                if not stored_hash:
                    # empty password/hash => authentication forbidden
                    return False
                result, updated_hash = crypt_context.verify_and_update(
                    password, stored_hash)
                if result:
                    if updated_hash:
                        # Added by Smile to save hash_password in database
                        env['admin.passwd'].create_or_set_passwd(updated_hash)
                    return True
    else:
        return native_verify_admin_password(self, password)


configmanager.set_admin_password = new_set_admin_password
configmanager.verify_admin_password = new_verify_admin_password
