# -*- coding: utf-8 -*-
# (C) 2021 Smile (<http://www.smile.fr>)
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl).


from odoo import fields, models, api, _
from odoo.exceptions import ValidationError


DEFAULT_ARCH_BASE = """<?xml version="1.0"?>
<data>
<!-- Insert modifications after this block -->

</data>
"""


class IrUiView(models.Model):
    _inherit = 'ir.ui.view'

    is_view_customize = fields.Boolean()
    is_view_generated = fields.Boolean()

    @api.model
    def open_custom_view(self, view_id, view_type, model_name):
        view_customize = self.env.ref(
            'smile_customize_data.ir_ui_view_form_view_customize')
        self = self.sudo()
        view_type = 'tree' if view_type == 'list' else view_type
        if view_id:
            view = self.browse(view_id).exists()
        elif not view_id and view_type and model_name:
            result = self.env[model_name].fields_view_get(view_type=view_type)
            view = self.create({
                'name': '{}_generate_{}'.format(
                    model_name.replace('.', '_'), view_type),
                'type': view_type,
                'model': model_name,
                'priority': 16,
                'mode': 'primary',
                'arch_base': result.get('arch'),
                'is_view_generated': True,
            })
        else:
            raise ValidationError(_(
                "The view was not found or could not be generated."))
        custom_view_name = '{}_custom_{}'.format(
            view.model.replace('.', '_'), view.type)
        custom_view_by_type = self.search([
            ('type', '=', view.type),
            ('model', '=', view.model),
            ('name', '=', custom_view_name),
        ], limit=1)
        if not custom_view_by_type:
            custom_view_by_type = self.create({
                'name': custom_view_name,
                'type': view.type,
                'model': view.model,
                'priority': 200,
                'mode': 'extension',
                'inherit_id': view.id,
                'arch_base': DEFAULT_ARCH_BASE,
                'is_view_customize': True,
            })
        return {
            'name': _('Customize view'),
            'type': 'ir.actions.act_window',
            'res_model': 'ir.ui.view',
            'res_id': custom_view_by_type.id,
            'views': [[view_customize.id, 'form']],
            'target': 'new',
            'context': {'no_customize': True}
        }

    def save_custom(self):
        return {'type': 'ir.actions.client', 'tag': 'reload'}
