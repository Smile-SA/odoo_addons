# -*- encoding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2010 Smile (<http://www.smile.fr>). All Rights Reserved
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

from osv import fields, osv

from smile_invoicing_plan.invoicing_plan_tools import compute_date


class wizard_change_commitment(osv.osv_memory):
    _name = 'wizard.change.commitment'
    _description = 'Change commitment'

    _columns = {
        'name': fields.many2one('sale.order.line', 'Subscription', required=True),
        'nb_periods': fields.integer('Nb periods')
    }

    def change_commitment(self, cr, uid, ids, context=None):
        for cc in self.browse(cr, uid, ids):
            commitment_end_date = cc.name.commitment_end_date
            if commitment_end_date:
                commitment_end_date = compute_date(commitment_end_date, cc.nb_periods)
                self.pool.get('sale.order.line').write(cr, uid, [cc.name.id], {'commitment_end_date': commitment_end_date})
        return {'type': 'ir.actions.act_window_close'}
wizard_change_commitment()
