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

import inspect

from openerp.osv import orm, fields


class IrModelMethods(orm.Model):
    _name = 'ir.model.methods'
    _description = 'Model Method'
    _order = 'name'

    _columns = {
        'name': fields.char('Method name', size=128, select=True, required=True),
        'model_id': fields.many2one('ir.model', 'Object', select=True, required=True, ondelete='cascade'),
    }

    def get_method_args(self, cr, uid, method_id, context=None):
        assert isinstance(method_id, (int, long)), 'method_id must be an integer'
        method = self.browse(cr, uid, method_id, context=context)
        model_class = self.pool.get(method.model_id.model).__class__
        original_method = getattr(model_class, method.name)
        return ', '.join(inspect.getargspec(original_method)[0])
