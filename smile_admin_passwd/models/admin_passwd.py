# -*- coding: utf-8 -*-
# (C) 2022 Smile (<https://www.smile.eu>)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import api, fields, models


class AdminPasswd(models.Model):
    _name = 'admin.passwd'

    password = fields.Char(required=True)

    @api.model
    def get_passwd(self):
        return self.search([], limit=1).password

    @api.model
    def create_or_set_passwd(self, new_password):
        self = self.sudo()
        admin_passwd = self.search([], limit=1)
        admin_passwd.write({
            'password': new_password
        }) if admin_passwd else self.create({
            'password': new_password
        })
