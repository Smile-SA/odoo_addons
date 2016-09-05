# -*- coding: utf-8 -*-

from odoo import fields, models


class OdooVersion(models.Model):
    _name = 'scm.version'
    _description = 'Odoo Version'
    _order = 'name'

    name = fields.Char(required=True)

    _sql_constraints = [
        ('unique_name', 'UNIQUE(name)', 'Odoo version must be unique'),
    ]
