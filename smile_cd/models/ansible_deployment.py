# -*- coding: utf-8 -*-

import inspect
import json
import logging
import os
import psutil
import shutil
from subprocess import Popen, CalledProcessError, STDOUT

import tempfile
from threading import Thread
import yaml

from odoo import api, fields, models, SUPERUSER_ID, _
from odoo.exceptions import UserError
from odoo.modules.registry import Registry
from odoo.tools import config
from odoo.tools.func import wraps

from odoo.addons.smile_docker.tools import get_exception_message, \
    with_new_cursor
from odoo.addons.smile_ci.tools import s2human

_logger = logging.getLogger(__name__)

STATES = [
    ('draft', 'Draft'),
    ('in_progress', 'In progress'),
    ('done', 'Done'),
]
RESULTS = [
    ('success', 'successful'),
    ('failure', 'failed'),
    ('killed', 'killed'),
]


def deployments_state_cleaner(setup_models):
    @wraps(setup_models)
    def new_setup_models(self, cr, *args, **kwargs):
        res = setup_models(self, cr, *args, **kwargs)
        callers = [frame[3] for frame in inspect.stack()]
        if 'preload_registries' not in callers:
            return res
        try:
            env = api.Environment(cr, SUPERUSER_ID, {})
            if 'ansible.deployment' in env.registry.models:
                Deployment = env['ansible.deployment']
                cr.execute(
                    "select relname from pg_class where relname='%s'"
                    % Deployment._table)
                if cr.rowcount:
                    _logger.info(
                        "Cleaning deployments in progress before restarting")
                    deployments_in_progress = Deployment.search(
                        [('state', '=', 'in_progress')])
                    deployments_in_progress.write(
                        {'state': 'done', 'result': 'killed'})
        except Exception as e:
            _logger.error(get_exception_message(e))
        return res
    return new_setup_models


class AnsibleDeployment(models.Model):
    _name = 'ansible.deployment'
    _description = 'Ansible Deployment'
    _inherit = ['mail.thread']
    _rec_name = 'revno'
    _order = 'create_date desc'

    def __init__(self, pool, cr):
        super(AnsibleDeployment, self).__init__(pool, cr)
        if getattr(Registry, '_deployments_state_cleaner', False):
            setattr(Registry, 'setup_models', deployments_state_cleaner(
                getattr(Registry, 'setup_models')))
        else:
            Registry._deployments_state_cleaner = True

    @property
    def deployments_path(self):
        return config.get('deployments_path') or tempfile.gettempdir()

    @api.one
    def _get_directory(self):
        self.directory = os.path.join(
            self.deployments_path, 'deployment_%s' % self.id)

    create_date = fields.Datetime('Created on', readonly=True)
    create_uid = fields.Many2one('res.users', 'Created by', readonly=True)
    branch_id = fields.Many2one(
        'scm.repository.branch', 'Branch', required=True,
        readonly=True, ondelete='cascade')
    build_id = fields.Many2one(
        'scm.repository.branch.build', 'Build',
        ondelete='set null', readonly=True,
        domain=[
            ('state', '=', 'done'),
            ('result', 'in', ('stable', 'unstable')),
        ])
    revno = fields.Char('Revision', required=True, readonly=True, states={
                        'draft': [('readonly', False)]})
    inventory_type_id = fields.Many2one(
        'ansible.inventory.type', 'Environment', required=True,
        readonly=True, states={'draft': [('readonly', False)]})
    state = fields.Selection(
        STATES, 'Status', required=True, default='draft',
        readonly=True, copy=False)
    result = fields.Selection(RESULTS, readonly=True, copy=False)
    logs = fields.Text(readonly=True, copy=False)
    directory = fields.Char(compute='_get_directory')
    date_planned = fields.Datetime('Planned date', readonly=True, states={
                                   'draft': [('readonly', False)]})
    date_start = fields.Datetime('Start date', readonly=True)
    date_stop = fields.Datetime('End date', readonly=True)
    time = fields.Integer(compute='_get_time')
    age = fields.Integer(compute='_get_age')
    time_human = fields.Char('Time', compute='_convert_time_to_human')
    age_human = fields.Char('Age', compute='_convert_age_to_human')
    ansible_inventory_type_ids = fields.Many2many(
        'ansible.inventory.type', string='Available environments',
        compute='_get_inventories')
    ansible_inventory_ids = fields.One2many(
        'ansible.inventory', 'branch_id', 'Inventories',
        compute='_get_inventories')
    pid = fields.Integer('Process Id', readonly=True)

    @api.one
    @api.depends('branch_id')
    def _get_inventories(self):
        branch = self.branch_id
        if branch.branch_tmpl_id and branch.use_branch_tmpl_to_deploy:
            branch = branch.branch_tmpl_id
        self.ansible_inventory_type_ids = branch.ansible_inventory_type_ids
        self.ansible_inventory_ids = branch.ansible_inventory_ids

    @api.one
    @api.depends('date_start', 'date_stop')
    def _get_time(self):
        if not self.date_start or (
                not self.date_stop and self.state in ('in_progress', 'done')):
            self.time = 0
        else:
            date_stop = self.date_stop or fields.Datetime.now()
            timedelta = fields.Datetime.from_string(date_stop) \
                - fields.Datetime.from_string(self.date_start)
            self.time = timedelta.total_seconds()

    @api.one
    @api.depends('date_start', 'date_stop')
    def _get_age(self):
        if not self.date_start:
            self.age = 0
        else:
            timedelta = fields.Datetime.from_string(fields.Datetime.now()) \
                - fields.Datetime.from_string(self.date_start)
            self.age = timedelta.total_seconds()

    @api.one
    def _convert_time_to_human(self):
        self.time_human = s2human(self.time, details=True)

    @api.one
    def _convert_age_to_human(self):
        self.age_human = s2human(self.age)

    @api.onchange('branch_id')
    def _onchange_branch(self):
        inventory_types = self.ansible_inventory_type_ids
        if len(inventory_types) == 1:
            self.inventory_type_id = inventory_types
        return {'domain': {
            'inventory_type_id': [('id', 'in', inventory_types.ids)]}}

    @api.onchange('build_id')
    def _onchange_build(self):
        self.revno = self.build_id.revno

    @api.multi
    def run(self):
        self._run()
        if len(self.ids) == 1 and self._context.get('popin'):
            return {
                'name': self._description,
                'type': 'ir.actions.act_window',
                'res_model': self._name,
                'view_type': 'form',
                'view_mode': 'form',
                'view_id': False,
                'res_id': self.id,
                'target': 'new',
                'context': self._context,
            }
        return True

    @api.one
    def _run(self, ignore_exceptions=False):
        branch_id = self.branch_id.id
        inventory_type_id = self.inventory_type_id.id
        if self._check_if_deployment_in_progress(branch_id, inventory_type_id):
            if ignore_exceptions:
                return
            else:
                raise UserError(_('Deployment already in progress'))
        revno = '#%s' % self.build_id.id if self.build_id else self.revno
        _logger.info('Deploying %s %s on %s...' %
                     (self.branch_id.display_name, revno,
                      self.inventory_type_id.name))
        self._make_directory()
        playbook = self._generate_ansible_playbook()
        inventory = self._generate_ansible_inventory()
        cmd = ['ansible-playbook', playbook, '-i', inventory, '--verbose']
        thread = Thread(target=self._execute_command, args=(cmd,))
        thread.start()

    @api.model
    @with_new_cursor(False)
    def _check_if_deployment_in_progress(self, branch_id, inventory_type_id):
        return self.search_count([
            ('branch_id', '=', branch_id),
            ('inventory_type_id', '=', inventory_type_id),
            ('state', '=', 'in_progress'),
        ])

    @api.multi
    @with_new_cursor(False)
    def _execute_command(self, cmd):
        result = 'failure'
        logs = ''
        try:
            with open(self._get_logfile(), 'w') as f:
                proc = Popen(cmd, stdout=f, stderr=STDOUT)
            self.write_with_new_cursor({
                'state': 'in_progress',
                'date_start': fields.Datetime.now(),
                'pid': proc.pid,
            })
            proc.wait()
            logs = self._get_logs()
            if 'failed=0' in logs and 'unreachable=0' in logs:
                result = 'success'
        except CalledProcessError as e:
            logs = e.output
        finally:
            self.write_with_new_cursor({
                'state': 'done',
                'date_stop': fields.Datetime.now(),
                'result': result,
                'logs': logs,
            })
            self._remove_directory()
            self._send_result()

    @api.multi
    def refresh_logs(self):
        try:
            self.logs = self._get_logs()
        except Exception:  # If subprocess is terminated
            pass
        return self.open_wizard() if self._context.get('popin') else True

    @api.multi
    def _get_logs(self):
        with open(self._get_logfile(), 'r') as f:
            return f.read()

    @api.multi
    def _get_logfile(self):
        self.ensure_one()
        return os.path.join(self.directory, 'ansible.log')

    @api.one
    def _make_directory(self):
        if not os.path.exists(self.directory):
            os.makedirs(self.directory)
        roles_path = os.path.join(self.directory, 'roles')
        if not os.path.exists(roles_path):
            os.makedirs(roles_path)
        roles = self.ansible_inventory_ids.mapped('role_id')
        for role in roles.filtered(lambda role: role.active):
            role.download_sources()
            role_path = os.path.join(roles_path, role.name)
            if not os.path.exists(role_path):
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
        for inventory in self.ansible_inventory_ids:
            if inventory.inventory_type_id == self.inventory_type_id and \
                    inventory.hosts:
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
        for inventory in self.ansible_inventory_ids:
            if inventory.inventory_type_id == self.inventory_type_id and \
                    inventory.hosts:
                content += '[%s]\n%s\n\n' % \
                    (inventory.role_id.name, inventory.hosts)
        return content

    @api.one
    @with_new_cursor(False)
    def _send_result(self):
        deployment_url = self._get_action_url(**{
            'res_id': self.id, 'model': self._name, 'view_type': 'form',
            'action_id': self.env.ref('smile_cd.action_branch_deployments').id,
        })
        template = self.env.ref('smile_cd.mail_template_deployment_result')
        self.with_context(
            deployment_url=deployment_url).message_post_with_template(
                template.id)

    @api.model
    def auto_run(self):
        deployments = self.search([
            ('state', '=', 'draft'),
            ('date_planned', '<=', fields.Datetime.now()),
        ])
        deployments._run(ignore_exceptions=True)
        return True

    @api.multi
    def save(self):
        return True

    @api.model
    @api.returns('self', lambda record: record.id)
    def update_or_create(self, vals):
        if vals['date_planned']:
            deployment = self.search([
                ('branch_id', '=', vals['branch_id']),
                ('inventory_type_id', '=', vals['inventory_type_id']),
                ('date_planned', '=', vals['date_planned']),
                ('state', '=', 'draft'),
            ], limit=1)
            if deployment:
                deployment.write(vals)
                return deployment
        return self.create(vals)

    @api.multi
    def kill(self):
        self._kill()
        return True

    @api.one
    def _kill(self):
        if self.pid:
            try:
                proc = psutil.Process(self.pid)
                proc.kill()
            except psutil.NoSuchProcess:
                pass
        self.write_with_new_cursor({
            'state': 'done',
            'date_stop': fields.Datetime.now(),
            'result': 'killed',
        })
