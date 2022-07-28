# -*- coding: utf-8 -*-
# (C) 2020 Smile (<http://www.smile.fr>)
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl).

from odoo import fields, models


class ResPartnerContactPointTag(models.Model):
    _name = 'res.partner.contact_point.tag'
    _inherit = 'res.partner.contact_point.mixin'
    _description = 'Contact Point Tag'

    name = fields.Char(translate=True)
