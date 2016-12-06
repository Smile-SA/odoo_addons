# -*- coding: utf-8 -*-

from odoo import fields, models


class DockerImage(models.Model):
    _inherit = 'docker.image'

    ansible_role_id = fields.Many2one('ansible.role', 'Role')
    ansible_role_vars = fields.Text('Variables')
    ansible_role_tags = fields.Char('Tags')
