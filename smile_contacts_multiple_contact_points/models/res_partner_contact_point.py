# -*- coding: utf-8 -*-
# (C) 2020 Smile (<http://www.smile.fr>)
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl).

from odoo import api, fields, models

from .res_partner_contact_point_mixin import CONTACT_POINT_TYPES


class ResPartnerContactPoint(models.Model):
    _name = 'res.partner.contact_point'
    _inherit = [
        'res.partner.contact_point.mixin',
        'mail.thread.blacklist',
        'mail.thread.phone',
    ]
    _description = 'Contact Point'

    def _get_default_tag(self):
        contact_point_type = self._context.get(
            'default_contact_point_type', False)
        return self.env['res.partner.contact_point.tag'].search([
            ('contact_point_type', '=', contact_point_type),
            ('is_default', '=', True),
        ], limit=1)

    partner_id = fields.Many2one(
        'res.partner', 'Contact', required=True, ondelete="cascade")
    tag_id = fields.Many2one(
        'res.partner.contact_point.tag', 'Tag', required=True,
        domain="[('contact_point_type', '=', contact_point_type)]",
        default=_get_default_tag)
    country_id = fields.Many2one('res.country', 'Country')
    email = fields.Char(compute='_compute_contact_point')
    phone = fields.Char(compute='_compute_contact_point')
    mobile = fields.Char(compute='_compute_contact_point')
    social_network = fields.Char(compute='_compute_contact_point')

    @api.depends('name', 'contact_point_type')
    def _compute_contact_point(self):
        for record in self:
            for cptype, label in CONTACT_POINT_TYPES:
                record[cptype] = record.name \
                    if record.contact_point_type == cptype else False

    def _sms_get_number_fields(self):
        return ['mobile', 'phone']

    @api.constrains('is_default', 'contact_point_type', 'partner_id')
    def _check_is_default(self):
        return super(ResPartnerContactPoint, self)._check_is_default()

    def _get_is_default_domain(self):
        self.ensure_one()
        return [('partner_id', '=', self.partner_id.id)] \
            + super(ResPartnerContactPoint, self)._get_is_default_domain()

    @api.model
    def create(self, vals):
        self._complete_vals(vals)
        return super(ResPartnerContactPoint, self).create(vals)

    @api.model
    def _complete_vals(self, vals):
        if not vals.get('tag_id'):
            vals['tag_id'] = self.env['res.partner.contact_point.tag'].search([
                ('contact_point_type', '=', vals.get('contact_point_type')),
                ('is_default', '=', True),
            ], limit=1).id
        if 'country_id' not in vals and \
                vals.get('contact_point_type') != 'email':
            vals['country_id'] = self.env['res.partner'].browse(
                vals.get('partner_id')).country_id.id

    def set_default(self):
        return self.write({'is_default': True})

    def _phone_get_number_fields(self):
        return ['mobile', 'phone']
