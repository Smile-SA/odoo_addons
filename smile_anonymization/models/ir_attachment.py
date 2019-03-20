# -*- coding: utf-8 -*-
# (C) 2019 Smile (<http://www.smile.fr>)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from openerp.osv import orm, fields

_DATA_MASK = "NULL where res_model is not null and res_model != 'ir.ui.view'"


class IrAttachment(orm.Model):
    _inherit = 'ir.attachment'

    _columns = {
        'name': fields.char(data_mask="'attachment_' || id::text"),
        'datas_fname': fields.char(data_mask="'attachment_' || id::text"),
        'description': fields.char(data_mask="NULL"),
        'db_datas': fields.char(data_mask=_DATA_MASK),
    }
