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

from openerp import tools
from openerp.osv import orm, fields


class SartreOperator(orm.Model):
    _name = 'sartre.operator'
    _description = 'Action Trigger Operator'

    _columns = {
        'name': fields.char('Name', size=30, required=True),
        'symbol': fields.char('Symbol', size=8, required=True),
        'opposite_symbol': fields.char('Opposite symbol', size=12, help="Opposite symbol for SQL filter"),
        'value_age_filter': fields.selection([('current', 'Current'), ('old', 'Old'), ('both', 'Both')], 'Value Age Filter', required=True),
        'native_operator': fields.selection([
            ('=', 'is equal to'), ('<=', 'less than'), ('>=', 'greater than'),
            ('like', 'contains (case-sensitive matching)'), ('ilike', 'contains (case-insensitive matching)'),
            ('in', 'in'), ('child_of', 'child of'), ('none', 'none'),
        ], 'Native Operator', required=True),
        'other_value_necessary': fields.boolean('Other Value Necessary'),
        'other_value_transformation': fields.char('Value Transformation', size=64, help="Useful only for native operator"),
        'expression': fields.text('Expression'),
    }

    _defaults = {
        'native_operator': 'none',
        'value_age_filter': 'both',
        'other_value_necessary': False,
    }

    @tools.cache(skiparg=3)
    def _get_operator(self, cr, uid, name):
        operator = opposite_operator = None
        if name.startswith('not '):
            opposite_operator = True
            name = name.replace('not ', '')
        operator_id = self.search(cr, uid, ['|', ('symbol', '=', name), ('opposite_symbol', '=', name)], limit=1)
        if operator_id:
            operator = self.browse(cr, uid, operator_id[0])
            if name == operator.opposite_symbol:
                opposite_operator = not opposite_operator
        return operator, opposite_operator

    def __init__(self, pool, cr):
        super(SartreOperator, self).__init__(pool, cr)
        self.clear_caches()

    def create(self, cr, uid, vals, context=None):
        operator_id = super(SartreOperator, self).create(cr, uid, vals, context)
        self.clear_caches()
        return operator_id

    def write(self, cr, uid, ids, vals, context=None):
        res = super(SartreOperator, self).write(cr, uid, ids, vals, context)
        self.clear_caches()
        return res

    def unlink(self, cr, uid, ids, context=None):
        res = super(SartreOperator, self).unlink(cr, uid, ids, context)
        self.clear_caches()
        return res
