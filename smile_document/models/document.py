# -*- encoding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2015 Smile (<http://www.smile.fr>). All Rights Reserved
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

from openerp import models, fields, api, _
from openerp.exceptions import Warning


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
        raise Warning(_('Attention : You cannot unlink document type!'))


class IrAttachement(models.Model):
    _inherit = 'ir.attachment'

    document_type_id = fields.Many2one('ir.attachment.type', string="Document Type")
    document_date = fields.Date(default=lambda self: fields.Date.today())
    expiry_date = fields.Date()
    archived = fields.Boolean()
    status = fields.Selection(STATUS, readonly=True, default='valid')

    @api.multi
    def _compute_document_status(self):
        for doc in self:
            status = 'valid'
            today = fields.Date.today()
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
