# -*- encoding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2014 Smile (<http://www.smile.fr>). All Rights Reserved
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

from openerp import api, fields, models, _
from openerp.exceptions import Warning

import openerp.addons.decimal_precision as dp


class ResUsers(models.Model):
    _inherit = 'res.users'

    commitment_global_limit = fields.Float('Global Commitment Limit', digits=dp.get_precision('Account'))
    commitment_limit_ids = fields.One2many('account.budget.post.commitment_limit', 'user_id', 'Commitment Limits')

    @api.one
    def check_commitment_limit(self, budget_post_id, amount):
        if not budget_post_id or not amount:
            return True
        warning_msg = _("You are not authorized to confirm this order.\nAmount for '%s' exceeds your commitment authorization")
        limits = [limit for limit in self.commitment_limit_ids if limit.budget_post_id.id == budget_post_id]
        if limits:
            for limit in limits:
                if limit.amount_limit < abs(amount):
                    raise Warning(warning_msg % limit.budget_post_id.display_name)
        elif self.commitment_global_limit < abs(amount):
            raise Warning(warning_msg % self.env['account.budget.post'].browse(budget_post_id).display_name)
        return True

    @api.model
    def search_users_with_commitment_authorizations(self, amount_by_budget_post):
        res = []
        cr = self._cr
        for budget_post_id, amount in amount_by_budget_post.iteritems():
            if not budget_post_id:
                continue
            cr.execute("SELECT user_id, amount_limit FROM account_budget_post_commitment_limit "
                       "WHERE budget_post_id = %s", (budget_post_id,))
            result = cr.dictfetchall()
            all_user_ids = [row['user_id'] for row in result]
            user_ids = [row['user_id'] for row in result if amount <= row['amount_limit']]
            if all_user_ids:
                cr.execute("SELECT id FROM res_users WHERE commitment_global_limit >= %s AND id not in %s",
                           (amount, tuple(all_user_ids)))
            else:
                cr.execute("SELECT id FROM res_users WHERE commitment_global_limit >= %s", (amount,))
            user_ids += [row[0] for row in cr.fetchall()]
            res.append(user_ids)
        return res and reduce(lambda x, y: x.intersection(y), (map(set, res))) or set()
