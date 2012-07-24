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

import inspect

from osv import osv, fields

def get_original_method(method):
    while method.func_closure:
        if method.__name__ != 'delegate_method':
            break
        method = method.func_closure[0].cell_contents
    return method

class IrModelMethods(osv.osv):
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
        original_method = get_original_method(getattr(model_class, method.name))
        return ', '.join(inspect.getargspec(original_method)[0])
IrModelMethods()

class IrModel(osv.osv):
    _inherit = 'ir.model'

    def update_methods_list(self, cr, uid, ids, context=None):
        if isinstance(ids, (int, long)):
            ids = [ids]
        for model_inst in self.read(cr, uid, ids, ['model'], context):
            model_id = model_inst['id']
            model = model_inst['model']
            obj = self.pool.get(model)
            method_names = [attr for attr in dir(obj) if inspect.ismethod(getattr(obj, attr)) and not attr.startswith('__')]
            method_obj = self.pool.get('ir.model.methods')
            method_ids = method_obj.search(cr, 1, [('model_id', '=', model_id), ('name', 'in', method_names)])
            existing_method_names = [method['name'] for method in method_obj.read(cr, uid, method_ids, ['name'])]
            for method in method_names:
                if method not in existing_method_names:
                    method_obj.create(cr, 1, {'name': method, 'model_id': model_id})
        return True
IrModel()
