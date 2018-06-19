# -*- coding: utf-8 -*-

from odoo import fields, models


class Tag(models.Model):
    _name = 'scm.repository.tag'
    _description = 'Repository Tag'
    _order = 'name'

    name = fields.Char(required=True, translate=True)
    color = fields.Integer()

    _sql_constraints = [
        ('unique_name', 'UNIQUE(name)', 'Repository tag must be unique'),
    ]
