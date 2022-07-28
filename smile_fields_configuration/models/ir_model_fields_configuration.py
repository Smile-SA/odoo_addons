# -*- coding: utf-8 -*-
# (C) 2021 Smile (<http://www.smile.fr>)
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl).

from odoo import fields, models, api


class IrModelFieldsConfiguration(models.Model):
    _name = 'ir.model.fields.configuration'
    _description = 'Fields configuration'
    _rec_name = 'field_id'

    field_id = fields.Many2one(
        'ir.model.fields', 'Field', index=True, ondelete="cascade",
        required=True)
    model_id = fields.Many2one(
        related='field_id.model_id', store=True, readonly=True)
    model = fields.Char(related='model_id.model', store=True, readonly=True)
    collected_by_etl = fields.Boolean()
    separator = fields.Char(string='Separator', default=',', readonly=True)
    collected_configuration_ids = fields.One2many('collected.configuration', 'field_configuration_id',
                                                  string='Collected pivot model')
    collected_column = fields.Char(string='Collected column')
    collected_extra_config = fields.Char(string='Collected extra config')
    distributed_by_etl = fields.Boolean()
    distributed_pivot_model_ids = fields.One2many('distributed.configuration', 'field_configuration_id',
                                                  string='Distributed pivot model')
    distributed_column = fields.Char(string='Distributed column')
    distributed_extra_config = fields.Char(string='Distributed extra config')
    referencial_ids = fields.One2many(
        'ir.referencial.line', 'configuration_id', string='Referencials')
    field_name = fields.Char(string='Name', related='field_id.name')
    field_description = fields.Char(string='Description', related='field_id.field_description')
    field_model_id = fields.Many2one('ir.model', string='Model', related='field_id.model_id')
    field_type = fields.Selection(string='Type', related='field_id.ttype')
    field_help = fields.Text(string='Help', related='field_id.help')
    field_required = fields.Boolean(string='Required', related='field_id.required')
    field_readonly = fields.Boolean(string='Readonly', related='field_id.readonly')
    field_store = fields.Boolean(string='Store', related='field_id.store')
    field_relation = fields.Char(string='Relation', related='field_id.relation')
    field_modules = fields.Char(related='field_id.modules')

    _sql_constraints = [
        ('field_uniq', 'unique (field_id)',
            "Only one configuration per field!"),
    ]

    @api.depends('field_id')
    def name_get(self):
        result = []
        for conf in self:
            result.append((conf.id, conf.field_id.display_name))
        return result
