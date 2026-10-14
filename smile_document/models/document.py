# -*- coding: utf-8 -*-
# (C) 2025 Smile (<http://www.smile.eu>)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import models, fields, api, _
from odoo.exceptions import UserError

STATUS = [('valid', 'Valid'),
          ('expired', 'Expired'),
          ('archived', 'Archived')]


class IrAttachementType(models.Model):
    _name = 'ir.attachment.type'
    _description = "Document type"

    name = fields.Char(required=True, translate=True)

    _unique_name = models.Constraint(
        'UNIQUE (name)', 'Document type name must be unique')

    def unlink(self):
        if self.env.context.get('force_unlink_doc_type'):
            return super().unlink()
        raise UserError(_('Attention : You cannot unlink document type!'))

    def copy(self, default=None):
        self.ensure_one()
        default = default or {}
        if not default.get('name'):
            default['name'] = _("%s (copy)", self.name)
        return super().copy(default)

class IrAttachement(models.Model):
    _inherit = 'ir.attachment'

    document_type_id = fields.Many2one(
        'ir.attachment.type', string="Document Type")
    document_date = fields.Date(default=lambda self: fields.Date.today())
    expiry_date = fields.Date()
    archived = fields.Boolean()
    status = fields.Selection(STATUS, readonly=True)

    def _compute_document_status(self):
        today = fields.Date.today()
        for doc in self:
            status = 'valid'
            if doc.archived:
                status = 'archived'
                if doc.expiry_date and doc.expiry_date > today:
                    doc.expiry_date = today
            elif doc.expiry_date:
                status = 'valid' if doc.expiry_date >= today else 'expired'
            if doc.status != status:
                doc.status = status
    @api.model_create_multi
    def create(self, vals_list):
        records = super().create(vals_list)
        records._compute_document_status()
        return records

    def write(self, values):
        res = super().write(values)
        self._compute_document_status()
        return res

    @api.model
    def update_document_status(self):
        today = fields.Date.today()
        self.search([
            ('expiry_date', '<', today),
            ('archived', '=', False),
        ])._compute_document_status()
