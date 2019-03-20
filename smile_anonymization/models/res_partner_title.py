# -*- coding: utf-8 -*-
# (C) 2019 Smile (<http://www.smile.fr>)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from openerp.osv import orm, fields


class ResPartnerTitle(orm.Model):
    _inherit = 'res.partner.title'

    _columns = {
        'name': fields.char(data_mask="'title_' || id::text"),
        'shortcut': fields.char(data_mask="NULL"),
    }
