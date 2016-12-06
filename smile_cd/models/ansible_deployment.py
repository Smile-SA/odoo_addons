# -*- coding: utf-8 -*-

import json
import logging
import os
import shutil
from subprocess import check_output, CalledProcessError
import tempfile
import yaml

from odoo import api, fields, models
from odoo.tools import config

_logger = logging.getLogger(__name__)

STATES = [
    ('draft', 'In progress'),
    ('done', 'Done'),
]
RESULTS = [
    ('success', 'Successful'),
    ('failure', 'Failed'),
]


class AnsibleDeployment(models.Model):
    _name = 'ansible.deployment'
    _description = 'Ansible Deployment'
    _rec_name = 'revno'
    _order = 'create_date desc'

    @property
    def deployments_path(self):
        return config.get('deployments_path') or tempfile.gettempdir()

    @api.one
    def _get_directory(self):
        self.directory = os.path.join(self.deployments_path, 'deployment_%s' % self.id)

    create_date = fields.Datetime('Created on', readonly=True)
    create_uid = fields.Many2one('res.users', 'Created by', readonly=True)
    branch_id = fields.Many2one('scm.repository.branch', 'Branch', required=True, readonly=True, ondelete='cascade')
    build_id = fields.Many2one('scm.repository.branch.build', 'Build', ondelete='set null',
                               domain=[('state', '=', 'done'), ('result', 'in', ('stable', 'unstable'))],
                               readonly=True, states={'draft': [('readonly', False)]})
    revno = fields.Char('Revision', required=True, readonly=True, states={'draft': [('readonly', False)]})
    inventory_type_id = fields.Many2one('ansible.inventory.type', 'Environment', required=True,
                                        readonly=True, states={'draft': [('readonly', False)]})
    state = fields.Selection(STATES, 'Status', required=True, default='draft', readonly=True, copy=False)
    result = fields.Selection(RESULTS, readonly=True, copy=False)
    logs = fields.Text(readonly=True, copy=False)
    directory = fields.Char(compute='_get_directory')

    @api.onchange('branch_id')
    def _onchange_branch(self):
        inventory_types = self.branch_id.ansible_inventory_type_ids
        if len(inventory_types) == 1:
            self.inventory_type_id = inventory_types
        return {'domain': {'inventory_type_id': [('id', 'in', inventory_types.ids)]}}

    @api.onchange('build_id')
    def _onchange_build(self):
        self.revno = self.build_id.revno

    @api.multi
    def run(self):
        self.ensure_one()
        self._make_directory()
        playbook = self._generate_ansible_playbook()
        inventory = self._generate_ansible_inventory()
        cmd = ['ansible-playbook', playbook, '-i', inventory, '--verbose']
        try:
            self.logs = check_output(cmd)
            self.result = 'success'
        except CalledProcessError, e:
            self.logs = e.output
            self.result = 'failure'
        finally:
            self.state = 'done'
        self._remove_directory()
        return self.open_wizard()

    @api.one
    def _make_directory(self):
        if not os.path.exists(self.directory):
            os.makedirs(self.directory)
        roles_path = os.path.join(self.directory, 'roles')
        if not os.path.exists(roles_path):
            os.makedirs(roles_path)
        roles = self.branch_id.ansible_inventory_ids.mapped('role_id')
        for role in roles.filtered(lambda role: role.active):
            role.download_sources()
            role_path = os.path.join(roles_path, role.name)
            os.symlink(role.directory, role_path)

    @api.one
    def _remove_directory(self):
        if self.directory and os.path.exists(self.directory):
            shutil.rmtree(self.directory)

    @api.multi
    def _generate_ansible_playbook(self):
        return self._generate_ansible_file('playbook')

    @api.multi
    def _generate_ansible_inventory(self):
        return self._generate_ansible_file('inventory')

    @api.multi
    def _generate_ansible_file(self, filetype):
        filename = getattr(self, '_get_ansible_%s_filename' % filetype)()
        filepath = os.path.join(self.directory, filename)
        content = getattr(self, '_generate_ansible_%s_content' % filetype)()
        with open(filepath, 'w') as f:
            f.write(content)
        return filepath

    @api.multi
    def _get_ansible_playbook_filename(self):
        return 'playbook.yml'

    @api.multi
    def _get_ansible_inventory_filename(self):
        return 'hosts'

    @api.multi
    def _generate_ansible_playbook_content(self):
        self.ensure_one()
        content = []
        for inventory in self.branch_id.ansible_inventory_ids:
            if inventory.hosts:
                role_infos = inventory.get_role_infos()
                if inventory.role_id.is_odoo:
                    role_infos['odoo_repo_rev'] = self.revno
                content.append({
                    'hosts': inventory.role_id.name,
                    'roles': [role_infos],
                })
        return yaml.dump(yaml.load(json.dumps(content)))

    @api.multi
    def _generate_ansible_inventory_content(self):
        self.ensure_one()
        content = ''
        for inventory in self.branch_id.ansible_inventory_ids:
            if inventory.inventory_type_id == self.inventory_type_id and inventory.hosts:
                content += '[%s]\n%s\n\n' % (inventory.role_id.name, inventory.hosts)
        return content
