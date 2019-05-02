# -*- encoding: utf-8 -*-
##############################################################################
#
# -*- coding: utf-8 -*-
# (C) 2019 Smile (<http://www.smile.eu>)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import models, fields, api, _
from odoo.exceptions import UserError
from dateutil.relativedelta import relativedelta

STATUS = [('valid', 'Valid'),
          ('expired', 'Expired'),
          ('archived', 'Archived')]


class IrAttachementType(models.Model):
    _name = 'ir.attachment.type'

    name = fields.Char(required=True, translate=True)

    _sql_constraints = [
        ('unique_name', 'UNIQUE (name)', _('Document type name must be unique')),
    ]

    @api.multi
    def unlink(self):
        if self._context.get('force_unlink_doc_type'):
            return super(IrAttachementType, self).unlink()
        raise UserError(_('Attention : You cannot unlink document type!'))

    @api.multi
    def copy(self, default=None):
        self.ensure_one()
        if default is None:
            default = {}
        if default.get('ir_attachmentname', '') in ['', self.name]:
            default['name'] = self.name + _(' (copy)')
        return super(IrAttachementType, self).copy(default)


class IrAttachement(models.Model):
    _name = 'ir.attachment'
    _inherit = 'ir.attachment'

    document_type_id = fields.Many2one('ir.attachment.type', string="Document Type")
    document_date = fields.Date(default=lambda self: fields.Date.today())
    expiry_date = fields.Datetime()
    archived = fields.Boolean()
    status = fields.Selection(STATUS, compute='_compute_document_status')

    @api.multi
    def _compute_document_status(self):
        for doc in self:
            status = 'valid'
            today = fields.Datetime.now()
            if doc.expiry_date:
                if doc.expiry_date >= today and not doc.archived:
                    status = 'valid'
                elif doc.expiry_date < today and not doc.archived:
                    status = 'expired'
            if doc.archived:
                status = 'archived'
                if doc.expiry_date > today:
                    doc.expiry_date = today
            if doc.status != status:
                doc.status = status

    @api.model
    def create(self, values):
        res = super(IrAttachement, self).create(values)
        res._compute_document_status()
        return res

    @api.multi
    def write(self, values):
        res = super(IrAttachement, self).write(values)
        self._compute_document_status()
        return res
