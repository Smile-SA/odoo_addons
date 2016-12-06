# -*- coding: utf-8 -*-

from odoo import api, fields, models
from odoo.tools.safe_eval import safe_eval


class AnsibleInventory(models.Model):
    _name = 'ansible.inventory'
    _description = 'Ansible Inventory'
    _rec_name = 'role_id'

    inventory_type_id = fields.Many2one('ansible.inventory.type', 'Environment', required=True, ondelete="restrict")
    role_id = fields.Many2one('ansible.role', 'Ansible role', required=True, ondelete="restrict")
    branch_id = fields.Many2one('scm.repository.branch', 'Branch', required=True)
    origin_id = fields.Reference([('scm.repository.branch', 'Branch'), ('scm.version.package', 'Package')], 'Origin')
    hosts = fields.Text()
    role_vars = fields.Text('Variables')
    role_tags = fields.Char('Tags')

    @api.multi
    def get_role_infos(self):
        self.ensure_one()
        role = self.role_id
        infos = {'role': role.name}
        tags = self.get_role_tags()
        if tags:
            infos['tags'] = tags
        infos.update(self.get_role_vars())
        if len(infos) == 1:
            return infos['role']
        return infos

    @api.multi
    def get_role_tags(self):
        def format_tags(tags):
            return tags and tags.replace(' ', '').split(',') or []
        self.ensure_one()
        role_tags = []
        for tags in (self.role_id.tags, self.origin_id.ansible_role_tags, self.role_tags):
            role_tags += format_tags(tags)
        return role_tags

    @api.multi
    def get_role_vars(self):
        def format_vars(vars):
            return safe_eval(vars or '{}', {'branch': self.branch_id})
        self.ensure_one()
        role_vars = {}
        for vars in (self.role_id.vars, self.origin_id.ansible_role_vars, self.role_vars):
            role_vars.update(format_vars(vars))
        return role_vars
