# -*- coding: utf-8 -*-

from odoo import fields, models


class OdooVersionPackage(models.Model):
    _inherit = 'scm.version.package'

    ansible_role_id = fields.Many2one('ansible.role', 'Ansible role', ondelete="set null")
    ansible_role_vars = fields.Text('Variables')
    ansible_role_tags = fields.Char('Tags')
