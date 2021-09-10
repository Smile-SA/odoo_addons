# -*- coding: utf-8 -*-
# (C) 2019 Smile (<https://www.smile.eu>)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields, models

_DATA_MASK = "NULL where res_model is not null and res_model != 'ir.ui.view'"


class IrAttachment(models.Model):
    _inherit = 'ir.attachment'

    name = fields.Char(data_mask="'attachment_' || id::text")
    datas_fname = fields.Char(data_mask="'attachment_' || id::text")
    description = fields.Text(data_mask="NULL")
    res_name = fields.Char(data_mask="'record_' || res_id::text")
    db_datas = fields.Binary(data_mask=_DATA_MASK)
