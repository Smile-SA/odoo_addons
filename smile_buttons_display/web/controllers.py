# -*- encoding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution    
#    Copyright (C) 2011 Smile (<http://www.smile.fr>). All Rights Reserved
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

from openobject.tools import expose
from openerp.controllers.form import Form
from openerp.widgets.listgrid import List
from openerp.utils import rpc

# Form View
native_form_create = Form.create

@expose(template="/openerp/controllers/templates/form.mako")
def new_form_create(self, params, tg_errors=None):
    for cell in native_form_create.im_func.func_closure:
        if isinstance(cell.cell_contents, type(lambda x: x)) and cell.cell_contents.func_name == 'create':
            res = cell.cell_contents(self, params, tg_errors)
            perms = rpc.session.execute('object', 'execute', 'ir.model.access', 'get_perms', params['_terp_model'], params['_terp_context'])
            res['buttons'].new = res['buttons'].new and bool(perms['create'])
            res['buttons'].edit = res['buttons'].edit and bool(perms['write'])
            res['buttons'].delete = res['buttons'].delete and bool(perms['unlink'])
            return res
    return native_form_create(self, params, tg_errors)

Form.create = new_form_create

# Tree View
native_list_init = List.__init__

def new_list_init(self, *args, **kwargs):
    native_list_init(self, *args, **kwargs)
    perms = rpc.session.execute('object', 'execute', 'ir.model.access', 'get_perms', kwargs['model'], kwargs['context'])
    self.dashboard = self.dashboard and bool(perms['create'])
    self.editable = self.editable and bool(perms['unlink'])
List.__init__ = new_list_init
