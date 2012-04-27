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
from openerp.utils import cache

# Form View
native_form_create = Form.create

@expose(template="/openerp/controllers/templates/form.mako")
def new_form_create(self, params, tg_errors=None):
    for cell in native_form_create.im_func.func_closure:
        if isinstance(cell.cell_contents, type(lambda x: x)) and cell.cell_contents.func_name == 'create':
            res = cell.cell_contents(self, params, tg_errors)
            res['buttons'].new = res['buttons'].new and cache.can_create(params['_terp_model']) and not params.get('_terp_context', {}).get('hide_create_button')
            res['buttons'].edit = res['buttons'].edit and cache.can_write(params['_terp_model']) and not params.get('_terp_context', {}).get('hide_write_button')
            res['buttons'].delete = res['buttons'].delete and cache.can_unlink(params['_terp_model']) and not params.get('_terp_context', {}).get('hide_unlink_button')
            res['buttons'].cancel = res['buttons'].cancel and not params.get('_terp_context', {}).get('hide_cancel_button')
            return res
    return native_form_create(self, params, tg_errors)

Form.create = new_form_create

# Tree View
native_list_init = List.__init__

def new_list_init(self, *args, **kwargs):
    native_list_init(self, *args, **kwargs)
    if kwargs.get('model'):
        self.dashboard = bool(self.dashboard) or not cache.can_create(kwargs['model']) or kwargs.get('context', {}).get('hide_create_button')
        self.editable = bool(self.editable) and cache.can_unlink(kwargs['model']) and not kwargs.get('context', {}).get('hide_unlink_button')
List.__init__ = new_list_init
