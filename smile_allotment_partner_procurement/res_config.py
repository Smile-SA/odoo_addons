# -*- encoding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2013 Smile (<http://www.smile.fr>). All Rights Reserved
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

from openerp.osv import fields, orm


class SaleConfiguration(orm.TransientModel):
    _inherit = 'sale.config.settings'

    _columns = {
        'picking_from_allotment_partner': fields.boolean('Generate a picking for each allotment partner',
            implied_group='smile_allotment_partner_procurement.group_allotment_partner'),
    }

    def execute(self, cr, uid, ids, context=None):
        installer = self.browse(cr, uid, ids[0], context)
        company = self.pool.get('res.users').browse(cr, uid, uid, context).company_id
        company.write({'picking_from_allotment_partner': installer.picking_from_allotment_partner})
        return super(SaleConfiguration, self).execute(cr, uid, ids, context)
