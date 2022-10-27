# -*- coding: utf-8 -*-
# (C) 2019 Smile (<http://www.smile.fr>)
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl).

from odoo import api, models
from ..models.anonymization import anonymize_object


class ConfirmAnonymization(models.TransientModel):
    _name = 'confirm.anonymization'
    _description = 'Confirm anonymization'

    def action_confirm(self):
        Partner = self.env['res.partner']
        if self._context and self._context.get('active_ids'):
            partners = Partner.browse(
                self._context.get('active_ids'))
            anonymize_fields = partners.get_anonymize_fields()
            for partner in partners:
                anonymize_object(
                    Partner, Partner._table, partner.id,
                    anonymize_fields.get('fields'),
                    anonymize_fields.get('phones'),
                    anonymize_fields.get('emails'))
            partners.write({'is_anonymized': True})
            fields_to_recompute = [
                item for sublist in anonymize_fields.values()
                for item in sublist
            ]
            partners.modified(fields_to_recompute)
            self.flush_model()
            partners.filtered(lambda partner: partner.active).toggle_active()
            return partners
        return False
