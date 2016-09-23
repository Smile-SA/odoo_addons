# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2015 Smile (<http://www.smile.fr>).
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

from openerp import api, fields, models


class ResCurrency(models.Model):
    _inherit = 'res.currency'

    in_letters_singular = fields.Char('In letters', help="For amounts written in letters (singular)")
    in_letters_plural = fields.Char('In letters', help="For amounts written in letters (plural)")

    @api.model
    def name_search(self, name='', args=None, operator='ilike', limit=100):
        domain = args and args[:] or []
        domain += [
            '|',
            '|',
            ('name', operator, name),
            ('in_letters_singular', operator, name),
            ('in_letters_plural', operator, name),
        ]
        recs = self.search(domain, limit=limit)
        return recs.name_get()
