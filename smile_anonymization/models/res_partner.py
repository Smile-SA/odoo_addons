# -*- coding: utf-8 -*-
# (C) 2019 Smile (<http://www.smile.fr>)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields, models


class ResPartner(models.Model):
    _inherit = 'res.partner'

    name = fields.Char(data_mask="'partner_' || id::text")
    commercial_company_name = fields.Char(data_mask="NULL")
    company_name = fields.Char(data_mask="NULL")
    display_name = fields.Char(data_mask="'partner_' || id::text")
    function = fields.Char(data_mask="NULL")
    vat = fields.Char(data_mask="NULL")
    ref = fields.Char(data_mask="NULL")
    street = fields.Char(data_mask="NULL")
    street2 = fields.Char(data_mask="NULL")
    email = fields.Char(data_mask="NULL")
    phone = fields.Char(data_mask="NULL")
    mobile = fields.Char(data_mask="NULL")
    website = fields.Char(data_mask="NULL")
