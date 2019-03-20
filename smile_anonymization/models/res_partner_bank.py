# -*- coding: utf-8 -*-
# (C) 2019 Smile (<http://www.smile.fr>)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from openerp.osv import orm, fields


class ResPartnerBank(orm.Model):
    _inherit = 'res.partner.bank'

    _columns = {
        'acc_number': fields.char(data_mask="'acc_number_' || id::text"),
    }
