# -*- coding: utf-8 -*-
# (C) 2021 Smile (<http://www.smile.fr>)
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl).

from odoo import fields, models, _, api


class IrModelFields(models.Model):
    _inherit = 'ir.model.fields'

    custom_group_operator = fields.Selection([
        ('sum', 'Sum'),
        ('avg', 'Average'),
    ], string='Group operator')
    configuration_ids = fields.One2many(
        'ir.model.fields.configuration', 'field_id', string='Configurations')

    def open_configuration(self):
        self.ensure_one()
        return {
            'name': _('Configuration'),
            'view_mode': 'form',
            'domain': [('field_id', '=', self.id)],
            'res_model': 'ir.model.fields.configuration',
            'res_id':
                self.configuration_ids[0].id if
                self.configuration_ids else False,
            'type': 'ir.actions.act_window',
            'context': {
                'default_field_id': self.id,
                'form_view_initial_mode': 'edit',
            },
        }

    def write(self, vals):
        if 'custom_group_operator' in vals:
            fields_to_update = self
            fields_to_update._write({
                'custom_group_operator':
                    vals.get('custom_group_operator') or None
            })
            del vals['custom_group_operator']
        return super(IrModelFields, self).write(vals)

    @api.model
    def _search(self, args, offset=0, limit=None, order=None, count=False, access_rights_uid=None):
        if self._context.get('field_relation_model'):
            model = self._context.get('field_relation_model')
            model_id = self.env['ir.model'].search([('model', '=', model)])
            args += [('model_id', '=', model_id.id), ('ttype', 'in', ['char', 'integer'])]
        return super()._search(args, offset, limit, order, count=count, access_rights_uid=access_rights_uid)
