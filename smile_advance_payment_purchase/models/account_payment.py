# -*- coding: utf-8 -*-
# (C) 2018 Smile (<http://www.smile.fr>)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import api, fields, models


class AccountPayment(models.Model):
    _inherit = 'account.payment'

    purchase_id = fields.Many2one(
        'purchase.order', 'Purchase Order',
        domain=[('state', '=', 'purchase')])

    @api.model
    def default_get(self, fields):
        """ Ensure that default choosen journal has the same company
        as the purchase, if the payment is created from purchase.
        """
        res = super(AccountPayment, self).default_get(fields)
        if not res.get('journal_id') and res.get('purchase_id'):
            is_advance_payment = res.get('is_advance_payment', False)
            company = self.env['purchase.order'].browse(
                res['purchase_id']).company_id
            jrnl_filters = self._compute_journal_domain_and_types()
            journal_types = jrnl_filters['journal_types']
            domain = [
                ('type', 'in', list(journal_types)),
                ('company_id', '=', company.id),
                ('is_advance_payment', '=', is_advance_payment),
            ]
            journal = self.env['account.journal'].search(domain, limit=1)
            res['journal_id'] = journal.id
        return res
