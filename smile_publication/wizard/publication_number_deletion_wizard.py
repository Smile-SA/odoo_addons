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


class PublicationNumberDeletionWizard(orm.TransientModel):
    _name = 'publication.number.deletion_wizard'
    _description = 'Publication number deletion wizard'

    _columns = {
        'publication_number_id': fields.many2one('publication.number', 'Publication Number', required=True),
        'shift_numbers': fields.boolean('Shift numbers'),
    }

    def button_validate(self, cr, uid, ids, context=None):
        assert len(ids) == 1, 'This option should only be used for a single id at a time.'
        wizard = self.browse(cr, uid, ids[0], context)
        wizard.publication_number_id.unlink()
        if wizard.shift_numbers:
            number = wizard.publication_number_id
            number_obj = self.pool.get('publication.number')
            number_ids = number_obj.search(cr, uid, [
                ('publication_id', '=', number.publication_id.id),
                ('publication_date', '>', number.publication_date),
            ], order="number asc", context=context)
            for number in number_obj.browse(cr, uid, number_ids, context):
                number.write({'number': int(number.number) - 1})
        return True
