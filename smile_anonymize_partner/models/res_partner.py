# -*- coding: utf-8 -*-
# (C) 2019 Smile (<http://www.smile.fr>)
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl).

from odoo import api, fields, models, _
from odoo.exceptions import AccessError


class ResPartner(models.Model):
    _inherit = 'res.partner'

    is_anonymized = fields.Boolean('Is Anonymized')

    def get_anonymize_fields(self):
        return {'fields': ['name', 'street', 'street2', 'comment'],
                'phones': ['phone', 'mobile'],
                'emails': ['email']}

    @api.multi
    def action_anonymization(self):
        if not self.env.user.has_group(
                'smile_anonymize_partner.group_anonymize_partner'):
            raise AccessError(
                _("You don't have access to do this action. "
                  "Please contact your system administrator."))
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'confirm.anonymization',
            'view_mode': 'form',
            'view_type': 'form',
            'view_id': self.env.ref(
                    'smile_anonymize_partner.confirm_anonymization_wizard').id,
            'target': 'new',
            'context': {'active_ids': self.ids},
        }
