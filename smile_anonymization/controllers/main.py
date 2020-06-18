# -*- coding: utf-8 -*-
# (C) 2020 Smile (<http://www.smile.fr>)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import http
from odoo.http import request
from odoo.addons.web.controllers.main import Database


class AnoDatabaseController(Database):
    @http.route('/web/database/backup', methods=['POST'],
                type='http', auth="none", csrf=False)
    def backup(self, master_pwd, name, backup_format='zip'):
        """ We're later calling odoo.service.db.exp_duplicate_database which
            end up closing connections to the current database.
            If we don't discard our cursor now, it'll try and commit in
            odoo.request.__exit__ and throw an exception. It'd lead to a
            corrupt .zip file and not dropping the temp database.
        """
        request._cr = None
        return super(AnoDatabaseController, self).backup(master_pwd, name,
                                                         backup_format)
