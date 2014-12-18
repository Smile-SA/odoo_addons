# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2014 Toyota Industrial Equipment SA
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

    disable_auto_subscribe = fields.Boolean(default=False, help='If checked, this partner will not receive notifications on instances he created')


class MailThread(models.Model):
    _inherit = 'mail.thread'

    @api.multi
    def message_subscribe(self, partner_ids, subtype_ids=None):
        # INFO: Disable author auto following if asked
        partner_ids_to_ignore = self.env['res.users'].search([('disable_auto_subscribe', '=', True)]).mapped('partner_id').ids
        partner_ids = [partner_id for partner_id in partner_ids if partner_id not in partner_ids_to_ignore]
        return super(MailThread, self).message_subscribe(partner_ids, subtype_ids)


class ResPartner(models.Model):
    _inherit = 'res.partner'

    notification_model_ids = fields.Many2many('ir.model', string='Notifications on', help='Models that the partner can follow')

    @api.one
    def follow_documents(self):
        if self.parent_id:
            followers_obj = self.env['mail.followers']
            # Unfollow all records of old notification models
            followers_obj.search([('partner_id', '=', self.id)]).unlink()
            # Follow all records of new notification models
            for model in self.notification_model_ids:
                if model.model in self.env.registry.models:
                    for record in self.env[model.model].with_context(active_test=False).search([('partner_id', '=', self.parent_id.id)]):
                        followers_obj.sudo().create({
                            'res_model': model.model,
                            'res_id': record.id,
                            'partner_id': self.id,
                        })

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
