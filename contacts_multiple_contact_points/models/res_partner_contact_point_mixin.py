# (C) 2020 Smile (<http://www.smile.fr>)
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl).

from odoo import api, fields, models, _
from odoo.exceptions import ValidationError

CONTACT_POINT_TYPES = [
    ('email', 'Email'),
    ('phone', 'Phone'),
]


class ResPartnerContactPointMixin(models.AbstractModel):
    _name = 'res.partner.contact_point.mixin'
    _description = 'Contact Point Mixin'

    name = fields.Char(required=True)
    sequence = fields.Integer(default=15)
    is_default = fields.Boolean()
    contact_point_type = fields.Selection(
        CONTACT_POINT_TYPES, "Type", required=True, default='phone')

    @api.constrains('is_default', 'contact_point_type')
    def _check_is_default(self):
        for record in self:
            if record.is_default:
                if self.search_count(record._get_is_default_domain()):
                    raise ValidationError(_("Default value must be unique!"))

    def _get_is_default_domain(self):
        self.ensure_one()
        return [
            ('id', '!=', self.id),
            ('is_default', '=', True),
            ('contact_point_type', '=', self.contact_point_type),
        ]

    @api.model_create_multi
    def create(self, vals_list):
        is_default_list = []
        for vals in vals_list:
            is_default = vals.get('is_default')
            is_default_list.append(is_default)
            if is_default:
                del vals['is_default']
        records = super().create(vals_list)
        for record, is_default in zip(records, is_default_list):
            if is_default:
                record.is_default = True
        return records

    def write(self, vals):
        if vals.get('is_default'):
            for record in self:
                self.search(record._get_is_default_domain()).write({
                    'is_default': False,
                })
        return super().write(vals)

    # TODO: force one default value per contact_point_type
