# -*- coding: utf-8 -*-

from odoo import api, fields, models


class ResPartner(models.Model):
    _inherit = 'res.partner'

    partner_type_id = fields.Many2one('res.partner.type', 'Partner Type')

    @api.multi
    def _update_children(self, vals):
        for partner in self:
            if partner.child_ids and partner.partner_type_id.field_ids:
                children_vals = {key: value for key, value in vals.iteritems()
                                 if key in partner.partner_type_id.field_ids.mapped('name')}
                if children_vals:
                    partner.child_ids.write(children_vals)

    @api.model
    def create(self, vals):
        new_partner = super(ResPartner, self).create(vals)
        new_partner._update_children(vals)
        return new_partner

    @api.multi
    def write(self, vals):
        res = super(ResPartner, self).write(vals)
        self._update_children(vals)
        return res
