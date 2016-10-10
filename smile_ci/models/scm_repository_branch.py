# -*- coding: utf-8 -*-

import base64
from datetime import datetime
from dateutil.relativedelta import relativedelta
import json
import logging
import os
import shutil
import yaml

from odoo import api, models, fields, tools, _
from odoo.exceptions import UserError, ValidationError
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT as DATETIME_FORMAT
from odoo.tools.safe_eval import safe_eval

from odoo.addons.smile_scm.tools import cd

from ..tools import cursor, with_new_cursor
from .scm_repository_branch_build import BUILD_RESULTS, CONFIGFILE, DOCKERFILE

_logger = logging.getLogger(__name__)

INTERVAL_TYPES = [
    ('years', 'years'),
    ('months', 'months'),
    ('weeks', 'weeks'),
    ('days', 'days'),
    ('hours', 'hours'),
    ('minutes', 'minutes'),
]


class Branch(models.Model):
    _inherit = 'scm.repository.branch'

    @api.model
    def _get_lang(self):
        return tools.scan_languages()

    @api.one
    def _get_last_build_result(self):
        for build in self.build_ids.filtered(lambda build: build.result != 'killed'):  # Because builds ordered by id desc
            if build.result:
                self.last_build_result = build.result
                break
        else:
            self.last_build_result = 'unknown'

    @api.model
    def _get_default_os(self):
        return self.env['scm.os'].sudo().search([], limit=1)

    @api.multi
    def _create_postgres_link(self, image):
        self.ensure_one()
        self.env['docker.link'].create({
            'name': 'db',
            'branch_id': self.id,
            'linked_image_id': image.id,
        })

    @api.one
    @api.depends('link_ids')
    def _get_postgres(self):
        postgres_image = self.link_ids.filtered(lambda link: link.name == 'db').linked_image_id
        if not postgres_image:
            postgres_image = self.env['docker.image'].sudo().search([('is_postgres', '=', True)], limit=1)
            self._create_postgres_link(postgres_image)
        self.postgres_id = postgres_image

    @api.one
    def _set_postgres(self):
        image_to_link = self.postgres_id
        self.link_ids.filtered(lambda link: link.name == 'db').unlink()
        self._create_postgres_link(image_to_link)

    @api.model
    def _get_default_docker_registry(self):
        # Store the current docker registry of the branch
        return self.env['docker.registry'].sudo().search([], limit=1)

    @api.one
    def _get_builds_count(self):
        self.builds_count = len(self.build_ids)

    @api.one
    def _get_is_filled_merge_with(self):
        self.has_branch_dependencies = bool(self.branch_dependency_ids)

    @api.one
    def _get_running_build(self):
        running_builds = self.build_ids.filtered(lambda build: build.state == 'running')
        if running_builds:
            self.running_build_id = running_builds.sorted(lambda build: build.date_start, reverse=True)[0]
        else:
            self.running_build_id = self.env['scm.repository.branch.build'].browse()

    @api.one
    @api.depends('branch')
    def _get_docker_image(self):
        self.docker_image = ''.join(char if char.isalnum() else '_'
                                    for char in self.display_name.lower()).replace('__', '_').rstrip('_')

    @api.one
    @api.depends('docker_registry_id.docker_host_id.base_url', 'docker_image')
    def _get_docker_registry_image(self):
        self.docker_registry_image = self.docker_registry_id.get_local_image(self.docker_image)

    @api.one
    def _get_docker_tags(self):
        tags = self.docker_registry_id.get_image_tags(self.docker_image)
        self.docker_tags = ', '.join(tags)

    @api.one
    @api.depends('docker_registry_image', 'link_ids')
    def _get_docker_compose_attachment(self):
        filename = 'docker-compose.yml'
        Attachment = self.env['ir.attachment']
        attachment = Attachment.search([
            ('name', '=', filename),
            ('res_model', '=', self._name),
            ('res_id', '=', self.id),
        ], limit=1)
        if attachment:
            self.docker_compose_attachment_id = attachment
        else:
            content = self.get_docker_compose_content()
            self.docker_compose_attachment_id = Attachment.create({
                'name': filename,
                'datas_fname': filename,
                'datas': base64.b64encode(content),
                'res_model': self._name,
                'res_id': self.id,
            })

    build_ids = fields.One2many('scm.repository.branch.build', 'branch_id', 'Builds', readonly=True, copy=False)
    builds_count = fields.Integer('Builds Count', compute='_get_builds_count', store=False)
    last_build_result = fields.Selection(BUILD_RESULTS + [('unknown', 'Unknown')], 'Last result',
                                         compute='_get_last_build_result', store=False)
    running_build_id = fields.Many2one('scm.repository.branch.build', 'Running build',
                                       compute='_get_running_build', store=False)

    # Build creation options
    use_in_ci = fields.Boolean('Use in Continuous Integration', copy=False)
    os_id = fields.Many2one('scm.os', 'Operating System', default=_get_default_os)
    postgres_id = fields.Many2one('docker.image', 'Database Management System', domain=[('is_postgres', '=', True)],
                                  compute='_get_postgres', inverse='_set_postgres')
    link_ids = fields.One2many('docker.link', 'branch_id', 'All linked services')
    other_link_ids = fields.One2many('docker.link', 'branch_id', 'Linked services',
                                     domain=[('name', '!=', 'db')])
    dump_id = fields.Many2one('ir.attachment', 'Dump file')
    modules_to_install = fields.Text('Modules to install')
    install_modules_one_by_one = fields.Boolean('Install and test modules one by one')
    install_demo_data = fields.Boolean(default=True, help='If checked, demo data will be installed')
    ignored_tests = fields.Text('Tests to ignore', help="Example: {'account': ['test/account_bank_statement.yml'], 'sale': 'all'}")
    server_path = fields.Char('Server path', default="server")
    addons_path = fields.Text('Addons path', default="addons", help="Comma-separated")
    code_path = fields.Text('Source code to analyse path', help="Addons path for which checking code quality and coverage.\n"
                                                                "If empty, all source code is checked.")
    test_path = fields.Text('Addons path to test', help="Exclusively run tests of modules defined inside these paths.\n"
                                                        "If empty, all modules installed will be tested.")
    workers = fields.Integer('Workers', default=0, required=True)
    user_uid = fields.Integer('Admin id', default=1, required=True)
    user_passwd = fields.Char('Admin password', default='admin', required=True)
    lang = fields.Selection('_get_lang', 'Language', default='en_US', required=True)
    system_packages = fields.Text('System packages')
    pip_packages = fields.Text('PyPI packages')
    npm_packages = fields.Text('Node.js packages')
    additional_options = fields.Text('Additional configuration options')

    # Branches merge options
    subfolder = fields.Char('Place current sources in')
    branch_dependency_ids = fields.One2many('scm.repository.branch.dependency', 'branch_id', 'Merge with')
    has_branch_dependencies = fields.Boolean(readonly=True, compute='_get_is_filled_merge_with')

    # Update interval
    nextcall = fields.Datetime(required=True, default=fields.Datetime.now())
    interval_number = fields.Integer('Interval Number', help="Repeat every x.", required=True, default=15)
    interval_type = fields.Selection(INTERVAL_TYPES, 'Interval Unit', required=True, default='minutes')

    # Docker
    docker_host_id = fields.Many2one('docker.host', 'Docker host', readonly=True, copy=False)
    docker_registry_id = fields.Many2one('docker.registry', 'Docker registry', readonly=True,
                                         default=_get_default_docker_registry, copy=False)
    docker_image = fields.Char(compute='_get_docker_image', store=True)
    docker_registry_image = fields.Char(compute='_get_docker_registry_image', store=True)
    docker_tags = fields.Char(compute='_get_docker_tags')
    docker_compose_attachment_id = fields.Many2one('ir.attachment', 'docker-compose.yml',
                                                   compute='_get_docker_compose_attachment')

    # Email receivers
    partner_ids = fields.Many2many('res.partner', string='Followers (including Repository Partners)',
                                   compute='_get_follower_partners', search='_search_partners')
    user_ids = fields.Many2many('res.users', string='Followers (Users)',
                                compute='_get_follower_partners', search='_search_users')

    @api.one
    @api.depends('message_follower_ids', 'repository_id.message_follower_ids')
    def _get_follower_partners(self):
        self.partner_ids = self.message_partner_ids | self.message_channel_ids.mapped('channel_partner_ids') | \
            self.repository_id.message_partner_ids | self.repository_id.message_channel_ids.mapped('channel_partner_ids')
        self.user_ids = self.partner_ids.mapped('user_ids')

    @api.model
    def _search_followers(self, operator, operand, field):
        followers = self.env['mail.followers'].sudo().search([
            ('res_model', 'in', [self._name, self.repository_id._name]),
            (field, operator, operand)])
        branch_followers = followers.filtered(lambda follower: follower.res_model == self._name)
        repository_followers = followers.filtered(lambda follower: follower.res_model == self.repository_id._name)
        return [
            '|',
            ('id', 'in', branch_followers.mapped('res_id')),
            ('repository_id', 'in', repository_followers.mapped('res_id')),
        ]

    @api.model
    def _search_partners(self, operator, operand):
        return self._search_followers(operator, operand, 'partner_id')

    @api.model
    def _search_users(self, operator, operand):
        return self._search_followers(operator, operand, 'partner_id.user_ids')

    @api.multi
    def toggle_use_in_ci(self):
        self.ensure_one()
        self.use_in_ci = not self.use_in_ci
        return True

    @api.multi
    def open(self):
        self.ensure_one()
        if not self.running_build_id:
            raise UserError(_('No running build'))
        return self.running_build_id.open()

    @api.onchange('branch_dependency_ids')
    def _onchange_branch_dependency_ids(self):
        self.has_branch_dependencies = bool(self.branch_dependency_ids)

    @api.onchange('version_id', 'os_id')
    def _onchange_version(self):
        os_ids = self.env['scm.version.package'].search([
            ('version_id', '=', self.version_id.id),
        ]).mapped('os_id.id')
        if self.os_id.id not in os_ids:
            self.os_id = False
        return {'domain': {'os_id': [('id', 'in', os_ids)]}}

    @api.one
    @api.constrains('use_in_ci', 'os_id')
    def _check_os_id(self):
        if self.use_in_ci and not self.os_id:
            raise ValidationError(_('Operating System is mandatory if branch is used in CI'))

    @api.one
    @api.constrains('ignored_tests')
    def _check_ignored_tests(self):
        if not self.ignored_tests:
            return
        if type(safe_eval(self.ignored_tests)) != dict:
            raise ValidationError(_("Please use a dict"))
        message = "Values must be of type: str, unicode or list of str / unicode"
        for value in safe_eval(self.ignored_tests).values():
            if type(value) == list:
                if filter(lambda element: type(element) not in (str, unicode), value):
                    raise ValidationError(_(message))
            elif type(value) not in (str, unicode):
                raise ValidationError(_(message))

    @api.one
    def _update(self):
        if self.state == 'draft':
            self.clone()
        else:
            self.pull()
        nextcall = datetime.strptime(fields.Datetime.now(), DATETIME_FORMAT)
        nextcall += relativedelta(**{self.interval_type: self.interval_number})
        self.nextcall = nextcall.strftime(DATETIME_FORMAT)

    @api.multi
    def _get_revno(self):
        self.ensure_one()
        return self.vcs_id.revno(self.directory, self.branch)

    @api.multi
    def _get_last_commits(self):
        self.ensure_one()
        last_revno = self.build_ids and self.build_ids[0].revno.encode('utf8') or self._get_revno()
        return self.vcs_id.log(self.directory, last_revno)

    @api.multi
    def _changes(self):
        self.ensure_one()
        if not self.build_ids or tools.ustr(self._get_revno()) != tools.ustr(self.build_ids[0].revno):  # Because builds ordered by id desc
            return True
        return False

    @api.one
    def create_build(self, force=False):
        self._create_build(force)
        return True

    @api.multi
    @with_new_cursor()
    def _create_build(self, force=False):
        self.ensure_one()
        self._try_lock(_('Build Creation already in progress'))
        if self.use_in_ci:
            self._update()
            if self._changes() or force is True:
                self.mapped('branch_dependency_ids.merge_with_branch_id')._update()
                vals = {'branch_id': self.id, 'revno': self._get_revno(), 'commit_logs': self._get_last_commits()}
                self.env['scm.repository.branch.build'].create(vals)

    @api.multi
    def force_create_build(self):
        self.create_build(force=True)
        return True

    @api.model
    def create_builds(self, force=False):
        """Method called by a scheduled action executed each X-minutes"""
        branches = self.search([('use_in_ci', '=', True), ('nextcall', '<=', fields.Datetime.now())])
        branches._create_builds(force)
        return True

    @api.multi
    @with_new_cursor()
    def _create_builds(self, force=False):
        for branch in self:
            try:
                branch.create_build(force)
            except Exception, e:
                _logger.error('Build creation failed for branch %s\n%s'
                              % (branch.display_name, repr(e)))

    @api.model
    def _get_purge_date(self, age_number, age_type):
        assert isinstance(age_number, (int, long))
        assert age_type in ('years', 'months', 'weeks', 'days', 'hours', 'minutes', 'seconds')
        last_creation_date = self.build_ids and self.build_ids[0].create_date
        if not last_creation_date:
            return False
        date = datetime.strptime(last_creation_date, DATETIME_FORMAT) + relativedelta(**{age_type: -age_number})
        return date.strftime(DATETIME_FORMAT)

    @api.one
    def _purge_builds(self, age_number, age_type):
        date = self._get_purge_date(age_number, age_type)
        if not date:
            return
        _logger.info('Purging builds created before %s for %s...' % (date, self.display_name))
        self.env['scm.repository.branch.build'].purge(date)

    @api.model
    def purge_builds(self, age_number=6, age_type='months'):
        """
        For each branch, get the last creation date of a build
        then remove builds older than this date minus [age_number age_type].

        @param age_number, integer: number of time
        @param age_type, integer: unit of time
        @return: True
        """
        for branch in self.search([]):
            branch._purge_builds(age_number, age_type)
        return True

    @api.multi
    def download_docker_image(self):
        self.ensure_one()
        if not self.docker_tags:
            raise UserError(_('No Docker image pushed to %s for %s') % (self.docker_registry_id.name, self.display_name))
        tags = self.docker_tags.split(', ')
        for tag in ('latest', 'base'):
            if tag in tags:
                tags.remove(tag)
        return {
            'type': 'ir.actions.client',
            'name': 'Download Docker image',
            'tag': 'download_docker_image',
            'target': 'new',
            'context': {
                'docker_registry_image': self.docker_registry_image,
                'docker_tags': ', '.join(tags),
                'default_tag': 'latest',
                'odoo_dir': self.os_id.odoo_dir,
                'attachment_id': self.docker_compose_attachment_id.id,
            },
        }

    @property
    def build_directory(self):
        self.ensure_one()
        return os.path.join(self.docker_host_id.builds_path, 'branch_%s' % self.id)

    @api.one
    def _create_build_directory(self):
        if self.build_directory and not os.path.exists(self.build_directory):
            os.makedirs(self.build_directory)

    @api.one
    def _remove_build_directory(self):
        if self.build_directory and os.path.exists(self.build_directory):
            shutil.rmtree(self.build_directory)

    @api.multi
    def _get_dockerfile_params(self):

        def format_packages(*packages):
            if not any(packages):
                return '; exit 0'
            return ' '.join(map(lambda pack: pack or '', packages))

        self.ensure_one()
        package = self.version_id.package_ids.filtered(lambda package: package.os_id == self.os_id)
        return {
            'system_packages': format_packages(package.system_packages),
            'pip_packages': format_packages(package.pip_packages,
                                            self.env['ir.config_parameter'].get_param('ci.flake8.extensions')),
            'npm_packages': format_packages(package.npm_packages),
            'specific_system_packages': format_packages(self.system_packages),
            'specific_pip_packages': format_packages(self.pip_packages),
            'specific_npm_packages': format_packages(self.npm_packages),
            'configfile': CONFIGFILE,
            'server_cmd': os.path.join(self.server_path, self.version_id.server_cmd),
            'odoo_dir': self.os_id.odoo_dir,
        }

    @api.one
    def _create_dockerfile(self):
        _logger.info('Generating dockerfile for %s:base...' % self.docker_image)
        content = base64.b64decode(self.os_id.dockerfile_base)
        localdict = self._get_dockerfile_params()
        with cd(self.build_directory):
            with open(DOCKERFILE, 'w') as f:
                f.write(content % localdict)

    @api.multi
    def _get_build_params(self):
        self.ensure_one()
        return {
            'path': self.build_directory,
            'tag': '%s:base' % self.docker_registry_image,
        }

    @api.one
    def _build_image(self):
        params = self._get_build_params()
        self.docker_host_id.build_image(**params)

    @api.multi
    def _get_push_params(self):
        self.ensure_one()
        return {'repository': self.docker_registry_image, 'tag': 'base'}

    @api.one
    def _push_image(self):
        params = self._get_push_params()
        self.docker_host_id.push_image(**params)

    @api.one
    def _remove_image(self):
        self.docker_host_id.remove_image('%s:base' % self.docker_registry_image, force=True)

    @api.one
    def _delete_image(self):
        self.docker_registry_id.delete_image(self.docker_registry_image, 'base')

    _docker_fields = ['use_in_ci', 'os_id', 'version_id', 'server_path',
                      'system_packages', 'pip_packages', 'npm_packages',
                      'branch_dependency_ids', 'subfolder']

    @api.multi
    def _store_in_registry(self, vals):
        branches = self.filtered(lambda branch: branch.os_id.dockerfile_base)
        for field in self._docker_fields:
            if field in vals:
                branches._delete_image()
                for branch in branches.filtered(lambda branch: branch.use_in_ci):
                    try:
                        branch.docker_host_id = self.env['docker.host'].get_default_docker_host()
                        branch._create_build_directory()
                        branch._create_dockerfile()
                        branch._build_image()
                        branch._remove_build_directory()
                        branch._push_image()
                        branch._remove_image()
                    except Exception, e:
                        msg = _("Base image creation failed\n\n%s") % repr(e)
                        with cursor(self._cr.dbname, False) as new_cr:
                            branch = branch.with_env(self.env(cr=new_cr))
                            branch.message_post(body=msg)
                            branch.use_in_ci = False
                        raise e
                    else:
                        msg = _("Base image successfully created")
                        with cursor(self._cr.dbname, False) as new_cr:
                            branch = branch.with_env(self.env(cr=new_cr))
                            branch.message_post(body=msg)
                break

    @api.model
    def create(self, vals):
        branch = super(Branch, self).create(vals)
        if branch.docker_image not in branch.docker_registry_id.get_images():
            branch._store_in_registry(vals)
        return branch

    @api.multi
    def write(self, vals):
        res = super(Branch, self).write(vals)
        self._store_in_registry(vals)
        return res

    @api.multi
    def unlink(self):
        self = self.sudo()
        self._delete_image()
        return super(Branch, self).unlink()

    @api.multi
    def get_docker_compose_content(self, tag='latest', container_name='', port='8069'):
        longpolling_port = '8071' if port == '8069' else str(int(port) + 1)
        services = {
            'odoo': {
                'image': '%s:%s' % (self.docker_registry_image, tag),
                'container_name': container_name,
                'ports': ['%s:8069' % port, '%s:8071' % longpolling_port],
                'links': self.mapped('link_ids.name'),
            }
        }
        services.update(self.mapped('link_ids').get_service_infos(self.docker_registry_image, tag))
        return yaml.dump(yaml.load(json.dumps({'version': '2', 'services': services})))

    @api.multi
    def recreate_image(self):
        branches = self.filtered(lambda branch: branch.use_in_ci)
        branches._store_in_registry({'use_in_ci': True})
        return True

    @api.multi
    @api.depends('message_follower_ids', 'repository_id.message_follower_ids')
    def _compute_is_follower(self):
        Followers = self.env['mail.followers'].sudo()
        followers = Followers.search([
            ('res_model', '=', self._name),
            ('res_id', 'in', self.ids),
            ('partner_id', '=', self.env.user.partner_id.id),
        ])
        following_ids = followers.mapped('res_id')
        parent_followers = Followers.search([
            ('res_model', '=', self and self[0].repository_id._name or ''),
            ('res_id', 'in', self.mapped('repository_id').ids),
            ('partner_id', '=', self.env.user.partner_id.id),
        ])
        parent_follower_ids = parent_followers.mapped('res_id')
        for branch in self:
            branch.message_is_follower = branch.id in following_ids or \
                branch.repository_id.id in parent_follower_ids

    @api.multi
    def message_unsubscribe_users(self, user_ids=None):
        res = super(Branch, self).message_unsubscribe_users(user_ids)
        self.mapped('repository_id').message_unsubscribe_users(user_ids)
        other_branches = self.mapped('repository_id.branch_ids') - self
        other_branches.message_subscribe_users(user_ids)
        return res
