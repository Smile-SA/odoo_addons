# -*- coding: utf-8 -*-
# (C) 2018 Smile (<http://www.smile.eu>)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import api, fields, models
from odoo.addons.account.models.account_invoice import TYPE2JOURNAL


class AccountInvoice(models.Model):
    _inherit = 'account.invoice'

    @api.model
    def _default_journal(self):
        journal = super(AccountInvoice, self)._default_journal()
        if journal or self._context.get('company_id'):
            return journal
        inv_type = self._context.get('type') or 'out_invoice'
        inv_types = inv_type if isinstance(inv_type, list) else [inv_type]
        journal_types = list(filter(None, map(TYPE2JOURNAL.get, inv_types)))
        company = self.env['res.company']._company_default_get(
            'account.invoice')
        domain = [
            ('type', 'in', journal_types),
            ('company_id', '=', company.id),
        ]
        return self.env['account.journal'].search(domain, limit=1)

    journal_id = fields.Many2one(default=_default_journal)
    company_id = fields.Many2one(domain=[('is_invoicing_company', '=', True)])
