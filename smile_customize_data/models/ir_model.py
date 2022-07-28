# -*- coding: utf-8 -*-
# (C) 2020 Smile (<http://www.smile.fr>)
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl).


from odoo import fields, models, api


class IrModel(models.Model):

    _inherit = "ir.model"

    is_customized_model = fields.Boolean(string='Customized model', compute='compute_customized_model',
                                         compute_sudo=True, store=True, readonly=False)

    @api.depends('state')
    def compute_customized_model(self):
        for model in self:
            if model.state == 'manual':
                model.is_customized_model = True
            else:
                model.is_customized_model = False

    @api.model
    def create(self, values):
        record = super().create(values)
        if record.is_customized_model:
            self.env['ir.model.access'].create({
                'name': 'access_{}'.format(record.model),
                'model_id': record.id,
                'perm_read': True,
                'perm_create': True,
                'perm_write': True,
                'perm_unlink': True,
            })
        return record
