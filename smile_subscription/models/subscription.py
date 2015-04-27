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

from openerp import models, fields, api


class SubscriptionSubscription(models.Model):
    _inherit = 'subscription.subscription'

    cron_id = fields.Many2one('ir.cron', string='Cron Job', help="Scheduler which runs on subscription", readonly=True,
                              ondelete='restrict', copy=False)

    @api.multi
    def set_process(self):
        for subscription in self:
            mapping = {'name': 'name',
                       'interval_number': 'interval_number',
                       'interval_type': 'interval_type',
                       'exec_init': 'numbercall',
                       'date_init': 'nextcall'}
            res = {'model': 'subscription.subscription',
                   'args': repr([[subscription.id]]),
                   'function': 'model_copy',
                   'priority': 6,
                   'user_id': subscription.user_id and subscription.user_id.id}
            for key, value in mapping.items():
                res[value] = eval('subscription.%s' % key)
            cron_id = subscription.cron_id
            vals = {'state': 'running'}
            if cron_id:
                cron_id.write(res)
            else:
                cron_id = self.env['ir.cron'].create(res)
                vals.update({'cron_id': cron_id.id})
        subscription.write(vals)
        return True
