# -*- coding: utf-8 -*-
# (C) 2020 Smile (<http://www.smile.fr>)
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl).

from odoo import api, fields, models

from .res_partner_contact_point_mixin import CONTACT_POINT_TYPES


class ResPartner(models.Model):
    _inherit = 'res.partner'

    contact_point_ids = fields.One2many(
        'res.partner.contact_point', 'partner_id', 'Contact Points')
    email = fields.Char(
        compute='_compute_contact_points', inverse='_set_email', store=True)
    phone = fields.Char(
        compute='_compute_contact_points', inverse='_set_phone', store=True)
    mobile = fields.Char(
        compute='_compute_contact_points', inverse='_set_mobile', store=True)

    @api.depends('contact_point_ids.name', 'contact_point_ids.is_default')
    def _compute_contact_points(self):
        for partner in self:
            for cptype, label in CONTACT_POINT_TYPES:
                partner[cptype] = partner.contact_point_ids.filtered(
                    lambda cp: cp.contact_point_type == cptype
                    and cp.is_default).name

    def _set_contact_point(self, contact_point_type):
        if self[contact_point_type]:
            contact_point = self.contact_point_ids.filtered(
                lambda cp: cp.name == self[contact_point_type] and
                cp.contact_point_type == contact_point_type)
            if not contact_point:
                self.contact_point_ids.create({
                    'name': self[contact_point_type],
                    'partner_id': self.id,
                    'contact_point_type': contact_point_type,
                    'is_default': True,
                })
            elif not contact_point.is_default:
                contact_point.is_default = True

    def get_fields_contact_points(self):
        return {'phone', 'mobile', 'email'}

    @api.model
    def create(self, values):
        partner = super().create(values)
        # Force recompute contact points
        # when update fields phone, mobile, email
        # (fields no recompute when insert two or more values)
        if self.get_fields_contact_points().intersection(values.keys()) and \
                not self._context.get('compute_contact_points'):
            partner.with_context(
                compute_contact_points=True)._compute_contact_points()
        return partner

    def write(self, values):
        result = super().write(values)
        # Force recompute contact points
        # when update fields phone, mobile, email
        # (fields no recompute when insert two or more values)
        if self.get_fields_contact_points().intersection(values.keys()) and \
                not self._context.get('compute_contact_points'):
            for partner in self:
                partner.with_context(
                    compute_contact_points=True)._compute_contact_points()
        return result

    def _set_email(self):
        self._set_contact_point('email')

    def _set_phone(self):
        self._set_contact_point('phone')

    def _set_mobile(self):
        self._set_contact_point('mobile')

    def action_show_contact_points(self):
        contact_point_type = self._context.get('default_contact_point_type')
        partner_id = self._context.get('default_partner_id')
        return {
            'name': "%ss" % dict(CONTACT_POINT_TYPES).get(contact_point_type),
            'type': 'ir.actions.act_window',
            'res_model': 'res.partner.contact_point',
            'view_mode': 'tree',
            'view_id': False,
            'domain': [
                ('contact_point_type', '=', contact_point_type),
                ('partner_id', '=', partner_id),
            ],
            'context': dict(self._context),
        }
