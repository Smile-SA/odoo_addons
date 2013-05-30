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

import time

from openerp.osv import orm, fields
from openerp.tools.translate import _


class HrContract(orm.Model):
    _inherit = "hr.contract"

    def _check_overlapping(self, cr, uid, ids, context=None):
        "Check if any other contract with the same employee overlap the current one"
        for contract in self.browse(cr, uid, ids, context):
            sibling_contract_ids = self.search(cr, uid, [('id', '!=', contract.id), ('employee_id', '=', contract.employee_id.id)], context=context)
            for sibling_contract in self.browse(cr, uid, sibling_contract_ids, context=context):
                # Current contract and siblings are unbound
                if not contract.date_end and not sibling_contract.date_end:
                    return False
                # Current contract is unbound
                if not contract.date_end and contract.date_start <= sibling_contract.date_end:
                    return False
                # One sibling contract is unbound
                if not sibling_contract.date_end and sibling_contract.date_start <= contract.date_end:
                    return False
                # Standard overlapping check
                if sibling_contract.date_start <= contract.date_end and sibling_contract.date_end >= contract.date_start:
                    return False
        return True

    _constraints = [
        (_check_overlapping, "A contract can't overlap another one with the same employee.", ['start_date', 'end_date', 'employee_id']),
    ]


class HrEmployee(orm.Model):
    _inherit = "hr.employee"

    def _get_latest_contract(self, cr, uid, ids, field_name, args, context=None):
        # Enforce date when getting the latest contract
        today = time.strftime('%Y-%m-%d')
        res = {}
        contract_obj = self.pool.get('hr.contract')
        for employee in self.browse(cr, uid, ids, context=context):
            # Search on closest date_start is enough: contract do not overlap
            contract_ids = contract_obj.search(cr, uid, [('date_start', '<=', today)], order='date_start', context=context)
            if contract_ids:
                res[employee.id] = contract_ids[-1:][0]
            else:
                res[employee.id] = False
        return res

    _columns = {
        # We need to copy the contract_id field definition from hr_contract/hr_contract.py, else the _get_latest_contract() method we're looking to overide gets linked to the field without being re-evaluated
        'contract_id': fields.function(_get_latest_contract, string='Contract', type='many2one', relation="hr.contract", help='Latest contract of the employee'),
        'job_id': fields.related('contract_id', 'job_id', type='many2one', relation='hr.job', string='Job', readonly=True),
    }
 