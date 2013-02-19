# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2011-2012 Smile (<http://www.smile.fr>).
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

from osv import osv


class MultiAccountsChartsWizard(osv.osv_memory):
    _inherit = 'wizard.multi.charts.accounts'

    def _create_fiscal_position(self, cr, uid, obj_multi, position, tax_template_ref, acc_template_ref, jnl_template_ref, context=None):
        fp_id = super(MultiAccountsChartsWizard, self)._create_fiscal_position(cr, uid, obj_multi, position, tax_template_ref, acc_template_ref,
                                                                               jnl_template_ref, context)
        jnl_fp_obj = self.pool.get('account.fiscal.position.journal')
        for jnl in position.journal_ids:
            vals = {
                'journal_src_id': jnl_template_ref[jnl.journal_src_id.id],
                'journal_dest_id': jnl_template_ref[jnl.journal_dest_id.id],
                'position_id': fp_id,
            }
            jnl_fp_obj.create(cr, uid, vals)
        return fp_id

MultiAccountsChartsWizard()
