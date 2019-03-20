# -*- coding: utf-8 -*-
# (C) 2019 Smile (<http://www.smile.fr>)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from openerp.osv import orm, fields


class ResUsers(orm.Model):
    _inherit = 'res.users'

    _columns = {
        'login': fields.char(data_mask="'user_' || id::text WHERE id != 1")
    }
