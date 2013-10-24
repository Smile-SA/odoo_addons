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

from openerp.osv import orm, fields


class PaymentMode(orm.Model):
    _name = 'account.payment.mode'
    _description = 'Payment Mode'

    _columns = {
        'name': fields.char('Name', size=64, required=True, translate=True),
        'code': fields.char('Code', size=12, required=True),
        'journal_id': fields.property(
            'account.journal',
            type='many2one',
            relation='account.journal',
            string="Journal",
            view_load=True,
            domain="[('type', '=', ('bank', 'cash'))]",
            required=True),
        'partner_bank_necessary': fields.boolean("Bank Account Necessary"),
        'active': fields.boolean('Active'),
    }

    _defaults = {
        'active': True,
    }

    _sql_constraints = [
        ('model_code', 'unique(code)', 'Payment mode code must be unique'),
    ]
