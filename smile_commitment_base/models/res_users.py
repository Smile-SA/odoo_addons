# -*- coding: utf-8 -*-

from functools import reduce

from odoo import api, fields, models, _
from odoo.exceptions import UserError

import odoo.addons.decimal_precision as dp


class ResUsers(models.Model):
    _inherit = 'res.users'

    commitment_global_limit = fields.Float(
        'Global Commitment Limit', digits=dp.get_precision('Account'),
        help="If equal to 0, the sky's the limit")
    commitment_limit_ids = fields.One2many(
        'account.budget.post.commitment_limit', 'user_id', 'Commitment Limits')

    @api.one
    def check_commitment_limit(self, budget_post_id, amount):
        if not budget_post_id or not amount:
            return True
        warning_msg = _("You are not authorized to confirm this order.\n"
                        "Amount for '%s' exceeds your commitment "
                        "authorization")
        limits = [limit for limit in self.commitment_limit_ids
                  if limit.budget_post_id.id == budget_post_id]
        if limits:
            for limit in limits:
                if limit.amount_limit < abs(amount):
                    raise UserError(warning_msg %
                                    limit.budget_post_id.display_name)
        elif self.commitment_global_limit and \
                self.commitment_global_limit < abs(amount):
            budget_post = self.env['account.budget.post'].browse(
                budget_post_id)
            raise UserError(warning_msg % budget_post.display_name)
        return True

    @api.model
    def search_users_with_commitment_authorizations(self,
                                                    amount_by_budget_post):
        """ Call this method to get users having commitment authorization
        @param amount_by_budget_post: dict with budget post id as key
            and total amount to commit as value

        @returns: set of user ids
        """
        res = []
        cr = self._cr
        for budget_post_id, amount in amount_by_budget_post.items():
            if not budget_post_id:
                continue
            cr.execute("SELECT user_id, amount_limit "
                       "FROM account_budget_post_commitment_limit "
                       "WHERE budget_post_id = %s", (budget_post_id,))
            result = cr.dictfetchall()
            all_user_ids = [row['user_id'] for row in result]
            user_ids = [row['user_id'] for row in result
                        if amount <= row['amount_limit']]
            if all_user_ids:
                cr.execute("SELECT id FROM res_users "
                           "WHERE commitment_global_limit >= %s "
                           "AND id not in %s",
                           (amount, tuple(all_user_ids)))
            else:
                cr.execute("SELECT id FROM res_users "
                           "WHERE commitment_global_limit >= %s", (amount,))
            user_ids += [row[0] for row in cr.fetchall()]
            res.append(user_ids)
        return res and \
            reduce(lambda x, y: x.intersection(y), (map(set, res))) or set()
