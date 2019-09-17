# -*- encoding: utf-8 -*-
# -*- coding: utf-8 -*-
# (C) 2019 Smile (<http://www.smile.eu>)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo import models, fields, api


class IrAttachment(models.Model):
    _inherit = 'ir.attachment'

    version_number = fields.Integer(readonly=True, string="Version number")

    @api.model
    def create(self, vals):
        res = super(IrAttachment, self).create(vals)
        for attachment in res.filtered(lambda l: l.datas):
            attachment.version_number = 1
        return res

    @api.multi
    def write(self, vals):
        res = super(IrAttachment, self).write(vals)
        if vals.get('datas'):
            for attachment in self:
                attachment.version_number += 1
        return res
