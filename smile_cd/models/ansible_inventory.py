# -*- coding: utf-8 -*-

from odoo import api, fields, models
from odoo.tools.safe_eval import safe_eval


class AnsibleInventory(models.Model):
    _name = 'ansible.inventory'
    _description = 'Ansible Inventory'
    _rec_name = 'role_id'

    inventory_type_id = fields.Many2one(
        'ansible.inventory.type', 'Environment',
        required=True, ondelete="restrict")
    role_id = fields.Many2one(
        'ansible.role', 'Ansible role', required=True, ondelete="restrict")
    branch_id = fields.Many2one(
        'scm.repository.branch', 'Branch', required=True, ondelete='cascade')
    origin_id = fields.Reference([
        ('scm.repository.branch', 'Branch'),
        ('scm.version.package', 'Package'),
    ], 'Origin')
    hosts = fields.Text()
    role_vars = fields.Text('Variables')

    @api.multi
    def get_role_vars(self):
        def format_vars(vars):
            branch = self.branch_id.branch_tmpl_id or self.branch_id
            return safe_eval(vars or '{}', {'branch': branch})
        self.ensure_one()
        role_vars = {}
        for vars in (self.role_id.vars, self.origin_id.ansible_role_vars,
                     self.role_vars):
            role_vars.update(format_vars(vars))
        return role_vars

    @api.multi
    def get_role_infos(self):
        self.ensure_one()
        role = self.role_id.name
        infos = self.get_role_vars()
        if not infos:
            return role
        infos['role'] = role
        return infos
