# -*- coding: utf-8 -*-

from odoo import fields, models


class DockerImage(models.Model):
    _inherit = "docker.image"

    is_postgres = fields.Boolean()
