# -*- coding: utf-8 -*-

from odoo import fields, models


class OperatingSystem(models.Model):
    _name = 'scm.os'
    _description = 'Operating System'

    name = fields.Char(required=True)
    sequence = fields.Integer(default=10)
    dockerfile = fields.Binary('Dockerfile template', required=True, help='Used to build Build image')
    dockerfile_base = fields.Binary('Dockerfile base template', help='Used to build Branch base image')
    odoo_dir = fields.Char('Odoo directory', required=True, default='/usr/src/odoo')
    active = fields.Boolean(default=True)
