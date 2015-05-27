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

from openerp.modules.registry import Registry

native_setup_models = Registry.setup_models


def new_setup_models(self, cr, partial=False):
    native_setup_models(self, cr, partial)
    for model_obj in self.models.itervalues():
        for fieldname, field in model_obj._fields.iteritems():
            if field.type == 'many2one' and field.ondelete and field.ondelete.lower() == 'cascade':
                if field.comodel_name.startswith('mail.'):
                    continue
                remote_obj = self.get(field.comodel_name)
                if not hasattr(remote_obj, '_cascade_relations'):
                    setattr(remote_obj, '_cascade_relations', {})
                remote_obj._cascade_relations.setdefault(model_obj._name, set()).add(fieldname)

Registry.setup_models = new_setup_models
