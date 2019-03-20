# -*- coding: utf-8 -*-
# (C) 2019 Smile (<http://www.smile.fr>)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from openerp.osv import orm, fields


class ResPartner(orm.Model):
    _inherit = 'res.partner'

    _columns = {
        'name': fields.char(data_mask="'partner_' || id::text", state='manual'),
        'display_name': fields.char(data_mask="'display_name_' || id::text"),
        'parent_name': fields.char(data_mask="NULL"),
        'birthdate': fields.char(data_mask="NULL"),
        'function': fields.char(data_mask="NULL"),
        'vat': fields.char(data_mask="NULL"),
        'ref': fields.char(data_mask="NULL"),
        'street': fields.char(data_mask="NULL"),
        'street2': fields.char(data_mask="NULL"),
        'email': fields.char(data_mask="NULL"),
        'phone': fields.char(data_mask="NULL"),
        'mobile': fields.char(data_mask="NULL"),
        'website': fields.char(data_mask="NULL"),
    }
