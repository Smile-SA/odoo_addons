# -*- coding: utf-8 -*-
# (C) 2021 Smile (<http://www.smile.fr>)
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl).

from odoo import fields, models, api, _
from odoo.exceptions import ValidationError


def get_default_id(self):
    field_model = self._context.get('field_relation_model')
    field_modules = self._context.get('field_relation_modules')
    if not field_modules or not field_model:
        return False
    for module in field_modules.split(', '):
        xml_id = '%s.field_%s__id' % (module, field_model.replace('.', '_'))
        field = self.env.ref(xml_id, raise_if_not_found=False)
        if field:
            return field
    return False


class BaseConfiguration(models.AbstractModel):
    _name = 'base.configuration'
    _description = 'Base configuration'
    _rec_name = 'collected_pivot_model_id'

    collected_pivot_model_id = fields.Many2one('collected.pivot.model', ondelete='restrict',
                                               string='Collected pivot model')
    field_configuration_id = fields.Many2one('ir.model.fields.configuration', ondelete='restrict', string='Field')
    functional_name = fields.Char(related='collected_pivot_model_id.functional_name')
    field_relation = fields.Char(related='field_configuration_id.field_relation')
    relation_field_id = fields.Many2one('ir.model.fields', string='Field to display',
                                        default=lambda self: get_default_id(self))

    @api.constrains('collected_pivot_model_id', 'field_configuration_id')
    def _check_collected_pivot_model_id(self):
        for record in self:
            if record.field_configuration_id and record.collected_pivot_model_id \
               and record.field_configuration_id.model != record.collected_pivot_model_id.model:
                raise ValidationError(_('This pivot model already used for another model!'))


class CollectedConfiguration(models.Model):
    _name = 'collected.configuration'
    _inherit = 'base.configuration'
    _description = 'Collected configuration'

    collected_unique_key = fields.Boolean(string='Collected unique key')
    default_value = fields.Char(string='Default value')
    field_type = fields.Selection(related='field_configuration_id.field_id.ttype')
    insertion_type = fields.Selection(string='insertion type',
                                      selection=[('create', "Create a new element if it doesn't exist"),
                                                 ('dont_create', "Don't create a new element if it doesn't exist")])


class DistributedConfiguration(models.Model):
    _name = 'distributed.configuration'
    _description = 'Distributed configuration'
    _inherit = 'base.configuration'

    collected_pivot_model_id = fields.Many2one(string='Target pivot model')
    distributed_domain = fields.Char(related='collected_pivot_model_id.distributed_domain',
                                     readonly=True, store=True)


class CollectedPivotModel(models.Model):
    _name = 'collected.pivot.model'
    _description = 'Collected Pivot Model'
    _rec_name = 'functional_name'

    functional_name = fields.Char()
    model = fields.Char()
    distributed_domain = fields.Char(default='[]')
