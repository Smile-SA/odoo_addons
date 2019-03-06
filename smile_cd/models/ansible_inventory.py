# -*- coding: utf-8 -*-

import os.path
import tempfile

from odoo import api, fields, models
from odoo.tools import config
from odoo.tools.safe_eval import safe_eval

from ..tools import AnsibleVault, password_generator


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
    vault_password = fields.Char(
        compute='_get_vault_password', inverse='_set_vault_password')
    vault_password_crypt = fields.Char(
        'Encrypted vault password', invisible=True, readonly=True)

    @api.one
    def _get_vault_password(self):
        if self.vault_password_crypt:
            self.vault_password = '*****'

    @api.one
    def _set_vault_password(self):
        if self.vault_password:
            self.vault_password_crypt = self._get_ansible_vault_cli(). \
                encrypt_string(self.vault_password)
        else:
            self.vault_password_crypt = False

    @api.model
    def _get_ansible_vault_cli(self):
        passfile = config.get('vault_passfile') or \
            os.path.join(tempfile.gettempdir(), '.vault_pass')
        if not os.path.isfile(passfile):
            with open(passfile, 'w') as f:
                f.write(password_generator())
        return AnsibleVault(passfile=passfile)

    @api.multi
    def _get_vault_passfile(self, directory):
        self.ensure_one()
        passfile = os.path.join(directory, '.vault_pass%s' % self.id)
        self._get_ansible_vault_cli(). \
            decrypt_string(self.vault_password_crypt, passfile)
        return passfile

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
