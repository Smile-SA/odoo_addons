# -*- coding: utf-8 -*-
# (C) 2011 Smile (<http://www.smile.fr>)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import api, models


def get_index(ordered_list, key):
    ordered_list = [i for i, j in ordered_list][::-1]
    return len(ordered_list) - ordered_list.index(key) - 1


class IrModel(models.Model):
    _inherit = 'ir.model'

    def _get_linked_models(self, models, required):
        linked_models = {}
        for model in models:
            linked_models.setdefault(model, {})
            for field_name, field in self.env[model]._fields.items():
                if field.type in ('many2one', 'many2many') and field.store \
                        and field.comodel_name in models and \
                        field.required == required:
                    linked_models[model].setdefault(
                        field.comodel_name, []).append('%s:id' % field_name)
        return linked_models

    def get_ordered_model_graph(self, models):
        ordered_models = []
        models = [model.model for model in models
                  if self.env[model.model]._auto and hasattr(
                      self.env[model.model], 'get_fields_to_export')]
        required_linked_models = self._get_linked_models(models, required=True)
        while required_linked_models:
            level_models = []
            for model in list(required_linked_models.keys()):
                if not required_linked_models[model]:
                    level_models.append((model, []))
                    del required_linked_models[model]
            for model in list(required_linked_models.keys()):
                for linked_model in list(required_linked_models[model].keys()):
                    if linked_model in dict(level_models):
                        del required_linked_models[model][linked_model]
            ordered_models.extend(level_models)

        not_required_linked_models = self._get_linked_models(
            models, required=False)
        for index, (model, model_fields) in enumerate(ordered_models):
            not_required_link_fields = sum(
                not_required_linked_models[model].values(), [])
            ordered_models[index] = (model, list(
                set(self.env[model].get_fields_to_export()) - set(
                    not_required_link_fields)))

        for model in not_required_linked_models:
            for linked_model, link_fields in not_required_linked_models[
                    model].items():
                index = get_index(ordered_models, model)
                if index > get_index(ordered_models, linked_model):
                    ordered_models[index] = (
                        model, ordered_models[index][1] + link_fields)
                else:
                    ordered_models.append((model, ['id'] + link_fields))

        return ordered_models


class IrModelData(models.Model):
    _inherit = 'ir.model.data'

    @api.model
    def _update(
            self, model, module, values, xml_id=False, store=True,
            noupdate=False, mode='init', res_id=False):
        """ Hack Odoo model data management to import module via web client
        """
        if 'id' not in values and 'complete_name' in values:
            module, name = values['complete_name'].split('.')
            model_data = self.search([
                ('module', '=', module), ('name', '=', name)], limit=1)
            if model_data:
                model_data.write(values)
            else:
                model_data = self.create(values)
            return model_data.id
        return super(IrModelData, self)._update(
            model=model, module=module, values=values, xml_id=xml_id,
            store=store, noupdate=noupdate, mode=mode, res_id=res_id)
