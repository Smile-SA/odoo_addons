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

from openerp.osv import orm


def get_index(l, k):
    l = [i for i, j in l][::-1]
    return len(l) - l.index(k) - 1


class IrModel(orm.Model):
    _inherit = 'ir.model'

    def _get_linked_models(self, models, required):
        linked_models = {}
        for model in models:
            linked_models.setdefault(model, {})
            for field_name, field in self.pool.get(model)._columns.iteritems():
                if field._type in ('many2one', 'many2many') and (not hasattr(field, 'store') or field.store) \
                        and field._obj in models and field._obj != model and field.required == required:
                    linked_models[model].setdefault(field._obj, []).append('%s:id' % field_name)
        return linked_models

    def get_model_graph(self, cr, uid, ids, context=None):
        "TODO: rename this method"
        ordered_models = []
        models = [model.model for model in self.browse(cr, uid, ids, context)
                  if self.pool.get(model.model)._auto and hasattr(self.pool.get(model.model), 'get_fields_to_export')]

        required_linked_models = self._get_linked_models(models, required=True)
        while required_linked_models:
            level_models = []
            for model in required_linked_models.keys():
                if not required_linked_models[model]:
                    level_models.append((model, []))
                    del required_linked_models[model]
            for model in required_linked_models.keys():
                for linked_model in required_linked_models[model].keys():
                    if linked_model in dict(level_models):
                        del required_linked_models[model][linked_model]
            ordered_models.extend(level_models)

        not_required_linked_models = self._get_linked_models(models, required=False)
        for index, (model, model_fields) in enumerate(ordered_models):
            not_required_link_fields = sum(not_required_linked_models[model].values(), [])
            ordered_models[index] = (model, list(set(self.pool.get(model).get_fields_to_export()) - set(not_required_link_fields)))

        for model in not_required_linked_models:
            for linked_model, link_fields in not_required_linked_models[model].iteritems():
                index = get_index(ordered_models, model)
                if index > get_index(ordered_models, linked_model):
                    ordered_models[index] = (model, ordered_models[index][1] + link_fields)
                else:
                    ordered_models.append((model, ['id'] + link_fields))

        return ordered_models
