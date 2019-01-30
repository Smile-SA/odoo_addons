# -*- coding: utf-8 -*-

import base64
from datetime import datetime
from dateutil.relativedelta import relativedelta
import inspect
import json
import logging
import os
from threading import Thread
import yaml

from odoo import api, fields, models, tools, SUPERUSER_ID, _
from odoo.exceptions import UserError, ValidationError
from odoo.modules.registry import Registry
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT as DATETIME_FORMAT
from odoo.tools.func import wraps
from odoo.tools.safe_eval import safe_eval

from odoo.addons.smile_docker.tools import format_image, format_repository, \
    get_exception_message, lock, with_new_cursor
from .scm_repository_branch_build import BUILD_RESULTS, CONFIGFILE

_logger = logging.getLogger(__name__)

INTERVAL_TYPES = [
    ('years', 'years'),
    ('months', 'months'),
    ('weeks', 'weeks'),
    ('days', 'days'),
    ('hours', 'hours'),
    ('minutes', 'minutes'),
]


def branches_in_registry_cleaner(setup_models):
    @wraps(setup_models)
    def new_setup_models(self, cr, *args, **kwargs):
        res = setup_models(self, cr, *args, **kwargs)
        callers = [frame[3] for frame in inspect.stack()]
        if 'preload_registries' not in callers:
            return res
        try:
            env = api.Environment(cr, SUPERUSER_ID, {})
            if 'scm.repository.branch' in env.registry.models:
                Branch = env['scm.repository.branch']
                cr.execute(
                    "select relname from pg_class where relname='%s'"
                    % Branch._table)
                if cr.rowcount:
                    _logger.info(
                        "Updating branches to find out which ones are "
                        "in registry before restarting")
                    for branch in Branch.search([]):
                        base_branch = branch.branch_tmpl_id or branch
                        image = format_image(base_branch.docker_image)
                        is_in_registry = 'base' in branch.docker_registry_id. \
                            get_image_tags(image)
                        if branch.is_in_registry != is_in_registry:
                            branch.is_in_registry = is_in_registry
        except Exception as e:
            _logger.error(get_exception_message(e))
        return res
    return new_setup_models


class Branch(models.Model):
    _name = 'scm.repository.branch'
    _inherit = ['scm.repository.branch', 'docker.image']
    _directory_prefix = 'branch'

    def __init__(self, pool, cr):
        super(Branch, self).__init__(pool, cr)
        if not getattr(Registry, '_branches_in_registry_cleaner', False):
            setattr(Registry, 'setup_models', branches_in_registry_cleaner(
                getattr(Registry, 'setup_models')))
        else:
            Registry._branches_in_registry_cleaner = True

    @api.model
    def _get_lang(self):
        return tools.scan_languages()

    @api.one
    def _get_last_build_result(self):
        last_build = self.env['scm.repository.branch.build'].search([
            ('branch_id', '=', self.id),
            ('result', 'not in', ('killed', '')),
            ('result', '!=', False),
        ], limit=1, order='id desc')
        self.last_build_result = last_build and last_build.result or 'unknown'

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
        postgres_image = self.link_ids.filtered(
            lambda link: link.name == 'db').linked_image_id
        if not postgres_image:
            postgres_image = self.env['docker.image'].sudo().search(
                [('is_postgres', '=', True)], limit=1)
            self._create_postgres_link(postgres_image)
        self.postgres_id = postgres_image

    @api.one
    def _set_postgres(self):
        image_to_link = self.postgres_id
        self.link_ids.filtered(lambda link: link.name == 'db').unlink()
        self._create_postgres_link(image_to_link)

    @api.one
    @api.depends('build_ids')
    def _get_builds_count(self):
        self.builds_count = self.env['scm.repository.branch.build']. \
            search_count([('branch_id', '=', self.id)])

    @api.one
    def _get_is_filled_merge_with(self):
        self.has_branch_dependencies = bool(self.branch_dependency_ids)

    @api.one
    def _get_running_build(self):
        self.running_build_id = self.env['scm.repository.branch.build'].search(
            [('branch_id', '=', self.id), ('state', '=', 'running')],
            limit=1, order='date_start desc')

    @api.one
    @api.depends('repository_id.name', 'branch')
    def _get_docker_image(self):
        image = ''.join(
            char if char.isalnum() else '_'
            for char in (self.display_name or '').lower()).replace(
                '__', '_').rstrip('_')
        self.docker_image = '%s:base' % image

    @api.one
    @api.depends('docker_registry_id.url', 'docker_image')
    def _get_docker_registry_image(self):
        self.docker_registry_image = self.docker_registry_id. \
            get_registry_image(self.docker_image)

    @api.one
    def _get_dockerfile(self):
        content = base64.b64decode(self.os_id.dockerfile_base or '')
        localdict = self._get_dockerfile_params()
        self.dockerfile = base64.b64encode(content % localdict)

    id = fields.Integer(readonly=True)
    # Because inherits docker.image
    name = fields.Char(related='repository_id.name', readonly=True)
    build_ids = fields.One2many(
        'scm.repository.branch.build', 'branch_id', 'Builds',
        readonly=True, copy=False)
    builds_count = fields.Integer(
        'Builds count', compute='_get_builds_count', store=False)
    last_build_result = fields.Selection(
        BUILD_RESULTS + [('unknown', 'Unknown')], 'Last result',
        compute='_get_last_build_result', store=False)
    running_build_id = fields.Many2one(
        'scm.repository.branch.build', 'Running build',
        compute='_get_running_build', store=False)

    # Build creation options
    use_in_ci = fields.Boolean('Used in Continuous Integration', copy=False)
    branch_tmpl_id = fields.Many2one(
        'scm.repository.branch', 'Template', auto_join=True,
        domain=[('branch_tmpl_id', '=', False)])
    os_id = fields.Many2one(
        'scm.os', 'Operating System')
    postgres_id = fields.Many2one(
        'docker.image', 'Database Management System',
        domain=[('is_postgres', '=', True)],
        compute='_get_postgres', inverse='_set_postgres')
    link_ids = fields.One2many(
        'docker.link', 'branch_id', 'All linked services')
    other_link_ids = fields.One2many(
        'docker.link', 'branch_id', 'Linked services',
        domain=[('name', '!=', 'db')])
    dump_id = fields.Many2one('ir.attachment', 'Dump file')
    modules_to_install = fields.Text('Modules to install')
    install_modules_one_by_one = fields.Boolean(
        'Install and test modules one by one')
    install_demo_data = fields.Boolean(
        default=True, help='If checked, demo data will be installed')
    ignored_tests = fields.Text(
        'Tests to ignore',
        help="Example: {'account': ['test/account_bank_statement.yml'], "
             "'sale': 'all'}")
    server_path = fields.Char('Server path', default="server")
    addons_path = fields.Text(
        'Addons path', default="addons", help="Comma-separated")
    code_path = fields.Text(
        'Source code to analyse path',
        help="Addons path for which checking code quality and coverage.\n"
             "If empty, all source code is checked.")
    test_path = fields.Text(
        'Addons path to test',
        help="Exclusively run tests of modules defined inside these paths.\n"
             "If empty, all modules installed will be tested.")
    workers = fields.Integer('Workers', default=0, required=True)
    user_uid = fields.Integer(related='version_id.user_uid', readonly=True)
    user_passwd = fields.Char('Admin password', default='admin', required=True)
    lang = fields.Selection('_get_lang', 'Language',
                            default='en_US', required=True)
    country_id = fields.Many2one(
        'res.country', 'Country', help="Useful from Odoo 9.0")
    system_packages = fields.Text('System packages')
    pip_packages = fields.Text('PyPI packages')
    pip_requirements = fields.Char(
        'PyPI requirements', default='requirements.txt')
    npm_packages = fields.Text('Node.js packages')
    additional_server_options = fields.Char(
        'Additional server options',
        default="--load=base,web,smile_test,smile_upgrade")
    additional_options = fields.Text('Additional configuration options')

    # Branches merge options
    subfolder = fields.Char('Place current sources in')
    branch_dependency_ids = fields.One2many(
        'scm.repository.branch.dependency', 'branch_id', 'Merge with')
    has_branch_dependencies = fields.Boolean(
        readonly=True, compute='_get_is_filled_merge_with')

    # Update interval
    nextcall = fields.Datetime(required=True, default=fields.Datetime.now())
    interval_number = fields.Integer(
        'Interval Number', help="Repeat every x.", required=True, default=15)
    interval_type = fields.Selection(
        INTERVAL_TYPES, 'Interval Unit', required=True, default='minutes')

    # Docker
    # required=False to allow branch creation
    docker_image = fields.Char(
        compute='_get_docker_image', store=True, required=False)
    docker_registry_image = fields.Char(compute='_get_docker_registry_image')
    dockerfile = fields.Binary(compute='_get_dockerfile')

    # Email receivers
    partner_ids = fields.Many2many(
        'res.partner', string='Followers (including Repository Partners)',
        compute='_get_follower_partners', search='_search_partners')
    user_ids = fields.Many2many(
        'res.users', string='Followers (Users)',
        compute='_get_follower_partners', search='_search_users')

    # Slack integration
    slack_integration = fields.Boolean()
    slack_webhook = fields.Char()
    slack_channel = fields.Char()
    slack_username = fields.Char(default='OdooCI')

    @api.one
    @api.depends('message_follower_ids', 'repository_id.message_follower_ids')
    def _get_follower_partners(self):
        self.partner_ids = self.message_partner_ids | \
            self.message_channel_ids.mapped('channel_partner_ids') | \
            self.repository_id.message_partner_ids | \
            self.repository_id.message_channel_ids.mapped(
                'channel_partner_ids')
        self.user_ids = self.partner_ids.mapped('user_ids')

    @api.model
    def _search_followers(self, operator, operand, field):
        followers = self.env['mail.followers'].sudo().search([
            ('res_model', 'in', [self._name, self.repository_id._name]),
            (field, operator, operand)])
        branch_followers = followers.filtered(
            lambda follower: follower.res_model == self._name)
        repository_followers = followers.filtered(
            lambda follower: follower.res_model == self.repository_id._name)
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

    @api.model
    def create(self, vals):
        if vals.get('version_id') and not vals.get('os_id'):
            vals['os_id'] = self.env['scm.version'].browse(
                vals['version_id']).default_os_id.id
        return super(Branch, self).create(vals)

    @api.multi
    def copy_data(self, default=None):
        default = default or {}
        default['postgres_id'] = self.postgres_id.id
        return super(Branch, self).copy_data(default)

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

    @api.onchange('version_id')
    def _onchange_version(self):
        os_ids = self.env['scm.version.package'].search([
            ('version_id', '=', self.version_id.id),
        ]).mapped('os_id.id')
        if self.os_id.id not in os_ids:
            self.os_id = self.version_id.default_os_id

    @api.one
    @api.constrains('use_in_ci', 'os_id', 'branch_tmpl_id')
    def _check_os_id(self):
        if self.branch_tmpl_id and self.search(
                [('branch_tmpl_id', '=', self.id)]):
            raise ValidationError(
                _('You cannot specify a template for a branch '
                  'which is a template for others'))
        branch = self.branch_tmpl_id or self
        if self.use_in_ci and not branch.os_id:
            raise ValidationError(
                _('Operating System is mandatory if branch is used in CI'))

    @api.one
    @api.constrains('ignored_tests')
    def _check_ignored_tests(self):
        if not self.ignored_tests:
            return
        if type(safe_eval(self.ignored_tests)) != dict:
            raise ValidationError(_("Please use a dict"))
        message = "Values must be of type: str, " \
                  "unicode or list of str / unicode"
        for value in safe_eval(self.ignored_tests).values():
            if type(value) == list:
                if list(filter(lambda element: type(element) not in
                               (str, unicode), value)):
                    raise ValidationError(_(message))
            elif type(value) not in (str, unicode):
                raise ValidationError(_(message))

    @api.one
    def _update(self):
        _logger.info('Updating sources for branch %s' % self.display_name)
        try:
            if self.state == 'draft':
                self.clone()
            else:
                self.pull()
        except UserError as e:
            error = get_exception_message(e)
            if "Could not find remote branch" in error:
                msg = _("Branch deactivated because "
                        "doesn't exist anymore\n\n%s") % error
                self._post_error_message(msg)
            raise
        else:
            nextcall = datetime.strptime(
                fields.Datetime.now(), DATETIME_FORMAT)
            nextcall += relativedelta(
                **{self.interval_type: self.interval_number})
            self.nextcall = nextcall.strftime(DATETIME_FORMAT)

    @api.one
    @with_new_cursor(False)
    def _post_error_message(self, msg):
        self.use_in_ci = False
        self.message_post(msg)

    @api.multi
    def get_revno(self):
        self.ensure_one()
        return self.vcs_id.revno(self.directory, self.branch)

    @api.multi
    def get_last_commits(self):
        self.ensure_one()
        last_build = self.env['scm.repository.branch.build'].search(
            [('branch_id', '=', self.id)], limit=1, order='id desc')
        last_revno = last_build and last_build.revno.encode('utf8') or ''
        try:
            return self.vcs_id.log(self.directory, last_revno)
        except Exception:
            return self.vcs_id.log(self.directory)

    @api.multi
    def check_if_revno_changed(self):
        self.ensure_one()
        revnos = self.env['scm.repository.branch.build'].search(
            [('branch_id', '=', self.id)]).mapped('revno')
        if not revnos or \
                tools.ustr(self.get_revno()) not in map(tools.ustr, revnos):
            return True
        return False

    @api.multi
    def create_build(self, force=False):
        for branch in self.filtered(lambda branch: branch.use_in_ci):
            if self._context.get('in_new_thread'):
                thread = Thread(
                    target=branch._create_build_with_new_cursor, args=(force,))
                thread.start()
            else:
                branch._create_build_locked(force)
        return True

    @api.one
    @with_new_cursor()
    def _create_build_with_new_cursor(self, force):
        self._create_build_locked(force)

    @api.one
    @lock('Build creation already in progress for branch %(name)s')
    def _create_build_locked(self, force):
        self._create_build(force)

    @api.multi
    def _copy_branch_followers_to_build(self, build, force):
        "Copy branch's follower to build"
        partner_ids = self.message_follower_ids.mapped('partner_id').ids
        generic_follower_vals = []
        for partner_id in partner_ids:
            generic_follower_vals.extend(
                self.message_follower_ids._add_follower_command(
                    build._name, build.ids, {partner_id: None}, {}, force)[0])
        build.write({'message_follower_ids': generic_follower_vals})
        subtype_id = self.env.ref('smile_ci.subtype_build_result').id
        specific_followers = self.message_follower_ids.search([
            ('res_model', '=', self._name),
            ('res_id', 'in', self.id),
            ('partner_id', 'in', partner_ids),
            ('subtype_ids', 'in', [subtype_id]),
        ])
        self.message_follower_ids.search([
            ('res_model', '=', build._name),
            ('res_id', '=', build.id),
            ('partner_id', 'in', specific_followers.mapped('partner_id').ids),
            ('subtype_ids', 'not in', [subtype_id]),
        ]).write({'subtype_ids': [(4, subtype_id)]})

    @api.one
    def _create_build(self, force):
        try:
            self._update()
            if self.check_if_revno_changed() or force is True:
                _logger.info('Creating build for branch %s' %
                             self.display_name)
                self.mapped(
                    'branch_dependency_ids.merge_with_branch_id')._update()
                vals = {
                    'branch_id': self.id,
                    'revno': self.get_revno(),
                    'commit_logs': self.get_last_commits(),
                }
                build = self.env['scm.repository.branch.build'].create(vals)
                self._copy_branch_followers_to_build(build, force)
        except Exception as e:
            msg = "Build creation failed"
            error = get_exception_message(e)
            _logger.error(msg + ' for branch %s\n\n%s' %
                          (self.display_name, error))
            self.message_post('\n\n'.join([_(msg), error]))

    @api.multi
    def force_create_build(self):
        self.create_build(force=True)
        return True

    @api.multi
    def create_builds(self, force=False):
        if not self:
            self = self.search([
                ('use_in_ci', '=', True),
                ('is_in_registry', '=', True),
                ('nextcall', '<=', fields.Datetime.now()),
            ])
        return self.create_build(force)

    @api.multi
    def _get_purge_date(self, age_number, age_type):
        assert isinstance(age_number, (int, long))
        assert age_type in ('years', 'months', 'weeks',
                            'days', 'hours', 'minutes', 'seconds')
        last_creation_date = self.env['scm.repository.branch.build'].search(
            [('branch_id', '=', self.id)], limit=1,
            order='create_date desc').create_date
        if not last_creation_date:
            return False
        date = datetime.strptime(
            last_creation_date, DATETIME_FORMAT) + relativedelta(
                **{age_type: -age_number})
        return date.strftime(DATETIME_FORMAT)

    @api.one
    def _purge_builds(self, age_number, age_type):
        date = self._get_purge_date(age_number, age_type)
        if not date:
            return
        _logger.info('Purging builds created before %s for %s...' %
                     (date, self.display_name))
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
    def generate_docker_compose_attachment(self, force_recreate=False,
                                           ignore_exceptions=False):
        try:
            self.ensure_one()
            attachment = self.env['ir.attachment'].search([
                ('datas_fname', '=', 'docker-compose.yml'),
                ('res_model', '=', self._name),
                ('res_id', '=', self.id)
            ], limit=1)
            if attachment and force_recreate:
                attachment.unlink()
            if not attachment or force_recreate:
                attachment = self._generate_docker_compose_attachment()
            return attachment
        except Exception as e:
            if not ignore_exceptions:
                raise
            _logger.error(e)

    @api.multi
    def _generate_docker_compose_attachment(self):
        self.ensure_one()
        filename = 'docker-compose.yml'
        content = self.get_docker_compose_content()
        return self.env['ir.attachment'].create({
            'name': filename,
            'datas_fname': filename,
            'datas': base64.b64encode(content or ''),
            'res_model': self._name,
            'res_id': self.id,
        })

    @api.multi
    def download_docker_image(self):
        self.ensure_one()
        image = format_image(self.docker_image)
        docker_registry = self.docker_registry_id
        if image not in docker_registry.get_images():
            raise UserError(_("No image in %s") % docker_registry.name)
        tags = docker_registry.get_image_tags(image)
        default_tag = 'latest' in tags and 'latest' or 'base'
        if default_tag in tags:
            tags.remove(default_tag)
        attachment = self.generate_docker_compose_attachment()
        return {
            'type': 'ir.actions.client',
            'name': 'Download Docker image',
            'tag': 'download_docker_image',
            'target': 'new',
            'context': {
                'docker_registry_insecure':
                    not docker_registry.url.startswith('https'),
                'docker_registry_auth_login': docker_registry.username,
                'docker_registry_auth_passwd': docker_registry.password,
                'docker_registry_url': docker_registry.url,
                'docker_registry_image':
                    format_repository(self.docker_registry_image),
                'docker_tags': ', '.join(tags),
                'default_tag': default_tag,
                'odoo_dir': self.os_id.odoo_dir,
                'attachment_id': attachment.id,
            },
        }

    @api.multi
    def _get_dockerfile_params(self):

        def format_packages(*packages):
            if not any(packages):
                return '; exit 0'
            return ' '.join(map(lambda pack: pack or '', packages))

        self.ensure_one()
        package = self.version_id.package_ids.filtered(
            lambda package: package.os_id == self.os_id)
        return {
            'system_packages': format_packages(package.system_packages),
            'pip_packages': format_packages(
                package.pip_packages, self.env['ir.config_parameter'].
                get_param('ci.flake8.extensions')),
            'npm_packages': format_packages(package.npm_packages),
            'specific_system_packages': format_packages(self.system_packages),
            'specific_pip_packages': format_packages(self.pip_packages),
            'specific_npm_packages': format_packages(self.npm_packages),
            'specific_pip_requirements': self.pip_requirements,
            'configfile': CONFIGFILE,
            'server_cmd': os.path.join(
                self.server_path or '', self.version_id.server_cmd),
            'odoo_dir': self.os_id.odoo_dir,
            'additional_server_options': '", "'.join(
                self.additional_server_options.split(' ')),
        }

    @api.multi
    def _check_pending_builds_to_remove(self):
        self.env['scm.repository.branch.build'].search([
            ('branch_id', 'in', self.ids),
            ('branch_id.use_in_ci', '=', False),
            ('state', '=', 'pending'),
        ]).unlink()

    _docker_compose_fields = [
        'docker_registry_image', 'link_ids', 'branch_tmpl_id']

    @api.multi
    def _check_docker_compose_attachment(self, vals):
        for field in self._docker_compose_fields:
            if field in vals:
                self.generate_docker_compose_attachment(force_recreate=True)

    _docker_fields = [
        'active', 'use_in_ci', 'os_id', 'version_id', 'server_path',
        'system_packages', 'pip_packages', 'npm_packages', 'pip_requirements',
        'branch_dependency_ids', 'subfolder', 'branch_tmpl_id']

    @api.multi
    def write(self, vals):
        res = super(Branch, self).write(vals)
        self._check_docker_compose_attachment(vals)
        self._check_pending_builds_to_remove()
        return res

    @api.multi
    def unlink(self):
        if self.env['scm.repository.branch.build'].search(
                [('branch_id', 'in', self.ids), ('state', '=', 'testing')]):
            raise UserError(
                _('You cannot delete a branch with a testing build'))
        self._remove_images_in_registry()
        return super(Branch, self.sudo()).unlink()

    @api.one
    def _remove_images_in_registry(self):
        """ Remove all tags of image in registry.
        """
        image = self.docker_image.split(':')[0]
        registry = self.docker_registry_id
        tags = registry.get_image_tags(image)
        for tag in tags:
            registry.delete_image(image, tag)

    @api.model
    def _get_images_to_store_domain(self):
        domain = super(Branch, self)._get_images_to_store_domain()
        return [('use_in_ci', '=', True)] + domain

    @api.multi
    @with_new_cursor(False)
    def _delete_base_images_in_registry(self):
        images_in_registry = self.filtered(lambda image: image.is_in_registry)
        base_images_to_delete = images_in_registry | \
            images_in_registry.mapped('branch_tmpl_id')
        # base_images_to_delete._delete_from_registry()
        self.search([('branch_tmpl_id', 'in', base_images_to_delete.ids)]). \
            write({'is_in_registry': False})

    @api.multi
    def store_in_registry(self):
        if not self:  # Scheduled action
            domain = self._get_images_to_store_domain()
            self = self.search(domain)
        else:  # Button -> delete base image in registry
            self._delete_base_images_in_registry()
        # INFO: launch store in registry for only one branch by template
        # and let scheduled action manage others
        images_to_store = self.browse()
        for image in self:
            if not image.branch_tmpl_id or \
                    image.branch_tmpl_id not in images_to_store.mapped(
                        'branch_tmpl_id'):
                images_to_store |= image
        for image in images_to_store:
            thread = Thread(target=image._store_in_registry_locked)
            thread.start()
        return True

    @api.one
    def _store_in_registry(self):
        try:
            if not self.branch_tmpl_id.is_in_registry:
                branch = self.branch_tmpl_id or self
                super(Branch, branch)._store_in_registry()
                for docker_host in self.env['docker.host'].search(
                        [('id', '!=', branch.docker_host_id.id)]):
                    docker_host.remove_image(branch.docker_registry_image)
                branch.message_post(_("Base image successfully created"))
            self.is_in_registry = True
            # INFO: do not force is_in_registry=True for others children
            # and let scheduled action manage them
        except Exception as e:
            self.use_in_ci = False
            msg = "Base image creation failed"
            error = get_exception_message(e)
            _logger.error(msg + ' for branch %s\n\n%s' %
                          (self.display_name, error))
            self.message_post('\n\n'.join([_(msg), error]))
        else:
            self._create_build(force=True)

    @api.multi
    def _get_build_params(self):
        params = super(Branch, self)._get_build_params()
        params['labels'] = {
            'odoo_version': self.version_id.name,
            'project': self.name,
            'repository': self.url,
            'branch': self.branch,
        }
        return params

    @api.multi
    def get_docker_compose_content(self, tag='latest', port=8069):
        ports = ['%s:8069' % port, '%s:8072' % (int(port) + 3)]
        services = self.get_service_infos(
            tag=tag, ports=ports, suffix=format_image(self.docker_image))
        return yaml.dump(yaml.load(json.dumps(
            {'version': '2.1', 'services': services})))

    @api.multi
    def get_service_infos(self, **kwargs):
        self.ensure_one()
        branch = self
        image = format_image(self.docker_image)
        default_tag = kwargs.get('tag') or 'latest'
        tags = self.docker_registry_id.get_image_tags(image)
        if default_tag not in tags and 'latest' in tags:
            default_tag = 'latest'
        if default_tag not in tags:
            branch = self.branch_tmpl_id or self
            default_tag = 'base'
        repository = format_repository(branch.docker_registry_image)
        kwargs['name'] = kwargs.get('name') or 'odoo'
        kwargs['repository'] = repository
        kwargs['tag'] = default_tag
        if default_tag == 'base':
            kwargs['with_persistent_storage'] = False
        services = super(Branch, self).get_service_infos(**kwargs)
        services[kwargs['name']].update({
            'image': '%s:%s' % (repository, kwargs['tag']),
            'stdin_open': True,  # To use pdb with docker attach
            'tty': True,  # To color stdout
        })
        return services

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
        if user_ids:
            user_partners = self.env['res.users'].browse(
                user_ids).mapped('partner_id')
            for repository in self.mapped('repository_id'):
                subscribors = user_partners & repository.message_partner_ids
                if subscribors:
                    repository.message_unsubscribe(subscribors.ids)
                    other_branches = repository.branch_ids - self
                    other_branches.message_subscribe(subscribors.ids)
        return res
