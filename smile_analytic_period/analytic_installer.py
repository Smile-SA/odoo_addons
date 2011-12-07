# -*- coding: utf-8 -*-
##############################################################################
#    
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2011-2012 Solucom (<http://solucom.fr>).
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

from osv import osv, fields
from tools.translate import _

class AnalyticInstaller(osv.osv_memory):
    _inherit = 'account.installer'

    _columns = {
        'analytic_period': fields.selection([('none', 'None'), ('global', 'Common for all companies'), ('specific', 'Specific to this company')], 'Analytic Periods', required=True),
    }

    _defaults = {
        'analytic_period': 'none',
    }

    def execute(self, cr, uid, ids, context=None):
        super(AnalyticInstaller, self).execute(cr, uid, ids, context)
        context = context or {}
        fiscalyear_obj = self.pool.get('account.fiscalyear')
        for wizard in self.read(cr, uid, ids, ['analytic_period', 'date_start', 'date_stop', 'company_id'], context, load='_classic_write'):
            if wizard['analytic_period'] != 'none':
                if wizard['analytic_period'] == 'specific' and not wizard['company_id']:
                    raise osv.except_osv(_('Warning!'), _('You cannot create specific analytic periods if you don\'t specify a company!'))
                domain = [
                    ('date_start', '=', wizard['date_start']),
                    ('date_stop', '=', wizard['date_stop']),
                    ('company_id', '=', wizard['company_id']),
                    ('period_ids', '!=', False),
                ]
                fiscalyear_ids = fiscalyear_obj.search(cr, uid, domain, context=context)
                context['analytic_period'] = wizard['analytic_period']
                fiscalyear_obj.create_analytic_periods(cr, uid, fiscalyear_ids, context)
AnalyticInstaller()
