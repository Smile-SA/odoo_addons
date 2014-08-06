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

import openerp.addons.decimal_precision as dp


class ResUsers(models.Model):
    _inherit = 'res.users'

    commitment_global_limit = fields.Float('Global Commitment Limit', digits=dp.get_precision('Account'))
    commitment_limit_ids = fields.One2many('account.budget.post.commitment_limit', 'user_id', 'Commitment Limits')

    @api.one
    def check_commitment_limit(self, budget_pos_id, amount):
        if not budget_pos_id or not amount:
            return True
        warning_msg = _("You are authorized to confirm this order.\nAmount for '%s' exceeds your commitment authorization")
        limits = [limit for limit in self.commitment_limit_ids if limit.budget_pos_id.id == budget_pos_id]
        if limits:
            for limit in limits:
                if limit.amount_limit < amount:
                    raise Warning(warning_msg % limit.budget_pos_id.display_name)
        elif self.commitment_global_limit < amount:
            raise Warning(warning_msg % limit.budget_pos_id.display_name)
        return True
