# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2015 Smile (<http://www.smile.fr>).
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

from openerp import api, fields, models


class ResUsers(models.Model):
    _inherit = 'res.users'

    disable_auto_subscribe = fields.Boolean(default=False, help='If checked, this user will not receive '
                                                                'notifications on instances he created')


class MailThread(models.Model):
    _inherit = 'mail.thread'

    @api.multi
    def message_subscribe(self, partner_ids=None, channel_ids=None, subtype_ids=None, force=True):
        # INFO: Disable author auto following if asked
        domain = [('disable_auto_subscribe', '=', True)]
        partner_ids_to_ignore = self.env['res.users'].search(domain).mapped('partner_id').ids
        partner_ids = [partner_id for partner_id in partner_ids if partner_id not in partner_ids_to_ignore]
        return super(MailThread, self).message_subscribe(partner_ids, channel_ids, subtype_ids, force)


class ResPartner(models.Model):
    _inherit = 'res.partner'

    @api.model
    def _get_notification_model_domain(self):
        models = []
        for model, obj in self.env.registry.models.iteritems():
            if hasattr(obj, '_follow_partner_fields'):
                models.append(model)
        return [('model', 'in', models)]

    notification_model_ids = fields.Many2many('ir.model', string='Notifications on',
                                              help='Models that the partner can follow',
                                              domain=_get_notification_model_domain)

    @api.multi
    def _get_contacts_to_notify(self):
        return self.mapped('child_ids')

    @api.multi
    def _get_contacts_parents(self):
        return self.mapped('parent_id')

    @api.one
    def follow_documents(self):
        parents = self._get_contacts_parents()
        if parents:
            # Follow all records of new notification models
            for model in self.notification_model_ids:
                if model.model in self.env.registry.models:
                    model_obj = self.env[model.model]
                    domain = []
                    if not hasattr(model_obj, '_follow_partner_fields'):
                        continue
                    for field in model_obj._follow_partner_fields:
                        domain.append((field, 'in', parents.ids))
                    if domain:
                        records = model_obj.with_context(active_test=False).search(domain)
                        records.message_subscribe(partner_ids=[self.id])

    @api.model
    def create(self, vals):
        record = super(ResPartner, self).create(vals)
        if 'notification_model_ids' in vals:
            record.follow_documents()
        return record

    @api.multi
    def write(self, vals):
        res = super(ResPartner, self).write(vals)
        if 'notification_model_ids' in vals:
            self.follow_documents()
        return res
