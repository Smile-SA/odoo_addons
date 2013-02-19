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

from osv import osv, fields

from base.ir.ir_sequence import _code_get


class IrSequenceTemplate(osv.osv):
    _name = "ir.sequence.template"
    _description = "Sequence Template"

    _columns = {
        'name': fields.char('Name', size=64, required=True),
        'code': fields.selection(_code_get, 'Code', size=64, required=True),
        'active': fields.boolean('Active'),
        'prefix': fields.char('Prefix', size=64, help="Prefix value of the record for the sequence"),
        'suffix': fields.char('Suffix', size=64, help="Suffix value of the record for the sequence"),
        'number_next': fields.integer('Next Number', required=True, help="Next number of this sequence"),
        'number_increment': fields.integer('Increment Number', required=True,
                                           help="The next number of the sequence will be incremented by this number"),
        'padding': fields.integer('Number padding', required=True,
                                   help="OpenERP will automatically adds some '0' on the left of the 'Next Number' to get "
                                   "the required padding size."),
    }

    _defaults = {
        'active': True,
        'number_next': 1,
        'number_increment': 1,
        'padding': 0,
    }

IrSequenceTemplate()
