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

from openerp import models


class ResUsers(models.Model):
    _inherit = 'res.users'

    def name_search(self, cr, uid, name='', args=None, operator='ilike', context=None, limit=100):
        if context and context.get('filter_budget_manager_for_purchase_order'):
            order_id = context['filter_budget_manager_for_purchase_order']
            purchase_order = self.pool['purchase.order'].browse(cr, uid, order_id, context)
            commitments_by_budget_post = purchase_order.get_commitments_by_budget_post()
            ids = self.search_users_with_commitment_authorizations(cr, uid, commitments_by_budget_post, context)
            args = (args or []) + [('id', 'in', list(ids))]
        return super(ResUsers, self).name_search(cr, uid, name, args, operator, context, limit)
