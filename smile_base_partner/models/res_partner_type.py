# -*- coding: utf-8 -*-

from odoo import fields, models


class ResPartnerType(models.Model):
    _name = 'res.partner.type'
    _description = 'Partner Type'

    name = fields.Char(required=True)
    active = fields.Boolean(default=True)
    field_ids = fields.Many2many('ir.model.fields', domain=[
        ('model', '=', 'res.partner'),
        ('store', '=', True),
        ('ttype', '!=', 'one2many'),
    ], string="Fields to update in children")
