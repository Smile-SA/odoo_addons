# -*- coding: utf-8 -*-

from odoo import fields, models


class AnsibleInventoryType(models.Model):
    _name = 'ansible.inventory.type'
    _description = 'Ansible Environment'

    name = fields.Char(required=True)
    sequence = fields.Integer('Priority', default=15)
    color = fields.Integer()

    _sql_constraints = [
        ('unique_name', 'UNIQUE(name)', 'Environment name must be unique'),
    ]
