# -*- coding: utf-8 -*-

import base64
import csv
from dateutil.relativedelta import relativedelta
from distutils.version import LooseVersion
from docker.errors import APIError
from functools import partial
import inspect
try:
    # For Python 2
    from cStringIO import StringIO
except ImportError:
    # For Python 3, warning: io.String exists in Py27
    from io import StringIO
import json
import logging
from lxml import etree
import os
import re
import requests
from six import string_types
import shutil
import sys
import tarfile
from threading import Lock, Thread
import time
try:
    # For Python 3
    from xmlrpc.client import Fault, ServerProxy
except ImportError:
    # For Python 2
    from xmlrpclib import Fault, ServerProxy

from odoo import api, models, fields, tools, _
from odoo.exceptions import UserError
import odoo.modules as addons

from odoo.addons.smile_docker.tools import \
    get_exception_message, with_new_cursor
from ..tools import mergetree, s2human

if sys.version_info > (3,):
    long = int

_logger = logging.getLogger(__name__)

BUILD_RESULTS = [
    ('stable', 'Stable'),
    ('unstable', 'Unstable'),
    ('failed', 'Failed'),
    ('killed', 'Killed'),
]
CONTAINER_SUFFIX = '_%s'
IMAGE_SUFFIX = ':%s'
IGNORE_PATTERNS = ['.*', '*~*', '*.py[cod]', '*sw[po]']
DBNAME = 'test'
CONFIGFILE = 'server.conf'
COVERAGEFILE = 'coverage.xml'
DOCKERFILE = 'Dockerfile'
FLAKE8FILE = 'flake8.log'
LOGFILE = 'server.log'
TESTFILE = 'scm.repository.branch.build.log.csv'
TEST_MODULE = 'smile_test'
DEBUGGER_ERROR_CODE = 'T002'


class Build(models.Model):
    _name = 'scm.repository.branch.build'
    _description = 'Build'
    _inherit = ['mail.thread', 'docker.stack']
    _rec_name = 'id'
    _order = 'id desc'
    _directory_prefix = 'build'

    def __init__(self, pool, cr):
        cls = type(self)
        cls._scheduler_lock = Lock()
        super(Build, self).__init__(pool, cr)

    @api.one
    @api.depends('docker_host_id.build_base_url', 'port')
    def _get_url(self):
        self.url = self.docker_host_id.get_build_url(self.port)

    @api.one
    @api.depends('date_start')
    def _get_time(self):
        if not self.date_start or \
                (not self.date_stop and self.state in ('running', 'done')):
            self.time = 0
        else:
            date_stop = self.date_stop or fields.Datetime.now()
            timedelta = fields.Datetime.from_string(date_stop) \
                - fields.Datetime.from_string(self.date_start)
            self.time = timedelta.total_seconds()

    @api.one
    @api.depends('date_start')
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

    @api.one
    def _get_last_build_time_human(self):
        last = self.search([
            ('branch_id', '=', self.branch_id.id),
            ('id', '<', self.id),
            ('result', 'in', ('unstable', 'stable')),
        ], limit=1)
        self.last_build_time_human = last.time_human if last else ''

    @api.one
    def _get_docker_image(self):
        self.docker_image = 'build:%s' % self.id

    @api.one
    def _get_failed_test_ratio(self):
        self.failed_test_ratio = '%s / %s' % (
            self.failed_test_count, self.test_count)

    @api.multi
    @api.depends('branch_id.build_ids.result')
    def _get_is_last(self):
        for build in self:
            if build.state in ('running', 'done') and \
                    build.result in ('stable', 'unstable'):
                build.is_last = build == build.branch_id.runnable_build_id
            else:
                build.is_last = False

    @api.one
    def _get_last_server_logs(self):
        branch = self.branch_id.branch_tmpl_id or self.branch_id
        filepath = os.path.join(branch.os_id.odoo_dir, LOGFILE)
        cmd = ['tail', '-n', self.server_logs_length, filepath]
        try:
            self.server_logs = self.docker_host_id.execute_command(
                self.docker_container, cmd)
        except Exception as e:
            self.server_logs = get_exception_message(e)

    @api.one
    def _get_image(self):
        self.image_id = self.branch_id

    @api.one
    def _get_dockerfile(self):
        branch = self.branch_id.branch_tmpl_id or self.branch_id
        content = base64.b64decode(branch.os_id.dockerfile or '')
        localdict = branch._get_dockerfile_params()
        localdict['base_image'] = branch.docker_registry_image
        self.dockerfile = base64.b64encode(content % localdict)

    name = fields.Char(default='Build')
    branch_id = fields.Many2one(
        'scm.repository.branch', 'Branch', required=True, readonly=True,
        index=True, ondelete='cascade', auto_join=True)
    image_id = fields.Many2one(
        'scm.repository.branch', compute='_get_image', required=False)
    revno = fields.Char('Revision', required=True, readonly=True)
    commit_logs = fields.Text('Last commits', readonly=True)
    create_uid = fields.Many2one('res.users', 'Created by', readonly=True)
    create_date = fields.Datetime('Created on', readonly=True)
    state = fields.Selection([
        ('pending', 'Pending'),
        ('testing', 'Testing'),
        ('running', 'Running'),
        ('done', 'Done'),
    ], 'Status', readonly=True, default='pending')
    result = fields.Selection(BUILD_RESULTS, 'Result', readonly=True)
    error = fields.Char(readonly=True)
    docker_registry_id = fields.Many2one(
        related='branch_id.docker_registry_id', readonly=True, store=True)
    docker_image = fields.Char(
        'Docker image', compute='_get_docker_image', related=None)
    dockerfile = fields.Binary(compute='_get_dockerfile')
    port = fields.Char(readonly=True)
    url = fields.Char(compute='_get_url')
    date_start = fields.Datetime('Start date', readonly=True)
    date_stop = fields.Datetime('End date', readonly=True)
    time = fields.Integer(compute='_get_time')
    age = fields.Integer(compute='_get_age')
    time_human = fields.Char('Time', compute='_convert_time_to_human')
    age_human = fields.Char('Age', compute='_convert_age_to_human')
    last_build_time_human = fields.Char(
        'Last build time', compute='_get_last_build_time_human')
    log_ids = fields.One2many(
        'scm.repository.branch.build.log', 'build_id', 'Logs', readonly=True)
    coverage_ids = fields.One2many(
        'scm.repository.branch.build.coverage', 'build_id',
        'Coverage', readonly=True)
    quality_code_count = fields.Integer(
        '# Quality errors', readonly=True, group_operator='avg')
    failed_test_count = fields.Integer(
        '# Failed tests', readonly=True, group_operator='avg')
    test_count = fields.Integer('# Tests', readonly=True, group_operator='avg')
    failed_test_ratio = fields.Char(
        'Failed tests ratio', compute='_get_failed_test_ratio')
    coverage_avg = fields.Float(
        'Coverage average', readonly=True, group_operator='avg')
    ppid = fields.Integer('Launcher Process Id', readonly=True)
    is_to_keep = fields.Boolean(
        "Keep alive", readonly=True,
        help="If checked, this build will not be stopped by scheduler")
    is_killable = fields.Boolean(
        "Can be killed", readonly=True,
        help="A build can only be killed if its container is started")
    server_logs = fields.Text(compute='_get_last_server_logs')
    server_logs_length = fields.Integer(default=30)
    is_last = fields.Boolean(compute='_get_is_last')

    @api.model
    def create(self, vals):
        context = {
            'mail_create_nolog': True,
            'mail_create_nosubscribe': True,
        }
        build = super(Build, self.with_context(**context)).create(vals)
        build._copy_sources()
        return build

    @api.multi
    def _get_branches_to_merge(self):
        self.ensure_one()
        base_branch = self.branch_id.branch_tmpl_id or self.branch_id
        branches = [(self.branch_id, base_branch.subfolder or '')]
        for dependency in base_branch.branch_dependency_ids:
            branches.append((dependency.merge_with_branch_id,
                             dependency.merge_subfolder or ''))
        return branches[::-1]

    @api.one
    def _copy_sources(self):
        _logger.info('Copying %s sources...' % self.branch_id.display_name)
        try:
            # Do not copy smile_test and useless files
            ignore_patterns = shutil.ignore_patterns(
                TEST_MODULE, *IGNORE_PATTERNS)
            for branch, subfolder in self._get_branches_to_merge():
                mergetree(branch.directory, os.path.join(
                    self.build_directory, subfolder), ignore=ignore_patterns)
            self._add_ci_addons()
        except Exception as e:
            _logger.error(get_exception_message(e))
            self._remove_directory()
            e.traceback = sys.exc_info()
            raise e

    @api.one
    def _add_ci_addons(self):
        for adp in addons.module.ad_paths:
            ci_addons_path = os.path.join(adp, 'smile_ci/addons')
            if os.path.exists(ci_addons_path):
                break
        else:
            raise IOError("smile_ci/addons is not found")
        ignore_patterns = shutil.ignore_patterns(*IGNORE_PATTERNS)
        dest = os.path.join(self.build_directory, 'ci-addons')
        mergetree(ci_addons_path, dest, ignore=ignore_patterns)

    @api.multi
    def _get_options(self):
        def format_str(path):
            if not path:
                return path
            # To avoid to update database when call replace method
            # A behaviour caused by new api
            path = path[:]
            return ','.join(map(
                lambda p: os.path.join(branch.os_id.odoo_dir, p),
                path.replace(' ', '').split(',')))

        self.ensure_one()
        branch = self.branch_id.branch_tmpl_id or self.branch_id
        return {
            'db_host': 'db',
            'db_port': 5432,
            'db_user': 'odoo',
            'db_password': 'odoo',
            'db_name': False,
            'logfile': format_str(LOGFILE),
            'coveragefile': format_str(COVERAGEFILE),
            'flake8file': format_str(FLAKE8FILE),
            'flake8_exclude_files': format_str(branch.flake8_exclude_files),
            'flake8_ignore_codes': format_str(branch.flake8_ignore_codes),
            'flake8_max_line_length': branch.flake8_max_line_length,
            'code_path': format_str(branch.code_path),
            'test_path': format_str(','.join(
                [branch.test_path or '', 'ci-addons'])),
            'addons_path': format_str(','.join(
                [branch.addons_path or '', 'ci-addons'])),
            'ignored_tests': branch.ignored_tests,
            'test_logfile': format_str(TESTFILE),
            'test_enable': False,
            'test_disable': True,
            'log_level': 'test',
            'log_handler': "[':TEST']",
            'admin_passwd': self.admin_passwd,
            'lang': branch.lang,
            'db_template': 'template0',
            'workers': branch.workers,
        }

    @api.one
    def _create_configfile(self):
        _logger.info('Generating %s for %s...' %
                     (CONFIGFILE, self.docker_image))
        branch = self.branch_id.branch_tmpl_id or self.branch_id
        options = self._get_options()
        filepath = os.path.join(self.build_directory, CONFIGFILE)
        with open(filepath, 'w') as cfile:
            cfile.write('[options]\n')
            for k, v in options.items():
                cfile.write('%s = %s\n' % (k, v))
            if branch.additional_options:
                cfile.write(branch.additional_options)

    @api.model
    def scheduler(self):
        with self._scheduler_lock:
            self._scheduler()
        return True

    @api.model
    def _scheduler(self):
        testing = self.search_count([('state', '=', 'testing')])
        max_testing = int(
            self.env['ir.config_parameter'].get_param('ci.max_testing'))
        max_testing_by_branch = int(
            self.env['ir.config_parameter'].
            get_param('ci.max_testing_by_branch'))
        builds_to_run = self.search([
            ('branch_id.use_in_ci', '=', True),
            ('branch_id.is_in_registry', '=', True),
            ('state', '=', 'pending'),
        ], order='id asc')
        builds_to_run = builds_to_run.filtered(
            lambda build: not build.branch_id.branch_tmpl_id or
            build.branch_id.branch_tmpl_id.is_in_registry)
        if builds_to_run:
            # Trigger only a build to run by branch in a same time
            safe_builds = self.browse(None)
            for build in builds_to_run:
                if build.branch_id not in safe_builds.mapped('branch_id'):
                    safe_builds |= build
            builds_to_run = safe_builds
            ###
            docker_hosts = builds_to_run.mapped('docker_host_id')
            ports = {dh.id: dh.find_ports() for dh in docker_hosts}
            builds_in_test = self.search([
                ('branch_id.use_in_ci', '=', True),
                ('state', '=', 'testing'),
            ], order='id asc')
        for build in builds_to_run:
            # Check max_testing_by_branch
            builds_by_branch = [
                b for b in builds_in_test if b.branch_id == build.branch_id]
            if len(builds_by_branch) >= max_testing_by_branch:
                continue
            # Check max_testing
            testing += 1
            if testing > max_testing:
                break
            # Use a new cursor to avoid concurrent update
            # if loop is longer than build test
            build.write_with_new_cursor({
                'state': 'testing',
                'result': '',
                'date_start': fields.Datetime.now(),
                'port': ports[build.docker_host_id.id].pop(),
                'ppid': os.getpid(),
            })
            # Use a new thread in order to launch other build tests
            # without waiting the end of the first one
            new_thread = Thread(target=build._test)
            new_thread.start()
            time.sleep(0.1)  # ?!!

    @api.multi
    @with_new_cursor(False)
    def _test(self):
        self.ensure_one()
        _logger.info('Testing build %s...' % self.id)
        try:
            self._create_configfile()
            self.start_container()
            # Ensure that Odoo is launched before calling services
            time.sleep(5)
            self._check_quality_code()
            self._count_lines_of_code()
            self._start_coverage()
            branch = self.branch_id.branch_tmpl_id or self.branch_id
            if branch.dump_id:
                self._restore_db()
            else:
                self._create_db()
            if branch.modules_to_install:
                modules_to_install = branch.modules_to_install.\
                    replace(' ', '').split(',')
                if not branch.install_modules_one_by_one:
                    modules_to_install = [modules_to_install]
                for module in modules_to_install:
                    if isinstance(module, string_types):
                        module = [module]
                    self._install_modules(module)
                    self._run_tests()
            else:  # E.g.: modules auto_install
                self._run_tests()
            self._stop_coverage()
            self._reactivate_admin()
        except Exception as e:
            self._set_to_failed(e)
            self._attach_files()
            self.remove_container()
        else:
            self._set_to_running()
            new_thread = Thread(target=self._check_running)
            new_thread.start()

    @api.one
    def _set_to_failed(self, e):
        if self.result == 'killed':
            return
        msg = get_exception_message(e)
        _logger.error(msg)
        self.write_with_new_cursor({
            'state': 'done',
            'result': 'failed',
            'port': '',
            'date_stop': fields.Datetime.now(),
            'error': '...%s' % msg[-77:],
        })
        self.with_context(build_error=msg)._send_build_result('Failed')

    @api.one
    @with_new_cursor(False)
    def _set_to_running(self):
        self.write({'state': 'running', 'date_stop': fields.Datetime.now()})
        self._attach_files()
        self._load_logs_in_db()
        self._generate_tests_report()
        self._set_build_result()
        if self.result in ('unstable', 'stable') and \
                self.docker_registry_id.active:
            self.delete_from_registry()
            self.store_in_registry()
            self.branch_id.generate_docker_compose_attachment(
                force_recreate=True, ignore_exceptions=True)

    @api.one
    @with_new_cursor(False)
    def _check_running(self):
        if not self.branch_id.version_id.web_included:
            self._kill_container()
        # Check max_running_by_branch
        self._check_max_running(domain=[('state', '=', 'running'),
                                        ('branch_id', '=', self.branch_id.id)],
                                param='ci.max_running_by_branch')
        # Check max_running
        self._check_max_running(domain=[('state', '=', 'running')],
                                param='ci.max_running')

    @api.model
    def _check_max_running(self, domain, param):
        running = self.search(domain, order='date_start desc')
        max_running = int(self.env['ir.config_parameter'].get_param(param))
        if len(running) > max_running:
            running_to_keep = running.filtered(lambda build: build.is_to_keep)
            max_running = max(max_running - len(running_to_keep), 0)
            running_not_to_keep = running - running_to_keep
            running_not_to_keep[max_running:]._kill_container()

    @property
    def admin_passwd(self):
        return self.env['ir.config_parameter'].get_param('ci.admin_passwd')

    @api.multi
    def _get_create_container_params(self):
        self.ensure_one()
        host_config = {'port_bindings': {8069: self.port}}
        params = super(Build, self)._get_create_container_params()
        params.update({
            'name': self.docker_container.replace('_%s' % self.id, ''),
            'suffix': self.id,
            'image': self.docker_image,
            'host_config': host_config,
            'labels': {
                'odoo_version': self.branch_id.version_id.name,
                'project': self.branch_id.name,
                'repository': self.branch_id.url,
                'branch': self.branch_id.branch,
                'revision': self.revno,
                'build': str(self.id),
            },
            'aliases': ['odoo'],
            'create_network': True,
        })
        return params

    @api.one
    def start_container(self):
        _logger.info('Starting container...')
        error = None
        tries = 2
        while tries:
            try:
                super(Build, self).start_container()
                break
            except Exception as error:
                _logger.error('Error during container starting: %s' % error)
                _logger.info(
                    'Try to remove unknown containers '
                    'before starting container...')
                self._remove_unknown_containers()
                tries -= 1
        else:
            raise error
        try:
            self._check_if_running()
            self.write_with_new_cursor({'is_killable': True})
        except Exception:
            logs = self.docker_host_id.get_logs(self.docker_container)
            _logger.error('Container %s logs:\n%s' %
                          (self.docker_container, logs))
            raise

    @property
    def starting_timeout(self):
        return int(self.env['ir.config_parameter'].get_param(
            'ci.odoo_starting_timeout', '60'))

    @api.one
    def _check_if_running(self):
        _logger.info('Check if container %s is running...'
                     % self.docker_container)
        timeout = self.starting_timeout
        t0 = time.time()
        sock_db = self._connect('db')
        while True:
            try:
                sock_db.server_version()
                break
            except Exception:
                if time.time() - t0 >= timeout:
                    _logger.error(
                        'Container %s exposed on port %s is not answering...'
                        % (self.docker_container, self.port))
                    raise

    @api.multi
    def _connect(self, service):
        self.ensure_one()
        xmlrpc = 'xmlrpc'
        if self.branch_id.version_id.standard_xmlrpc:
            xmlrpc = 'xmlrpc/2'
        url = '%s/%s/%s' % (self.url, xmlrpc, service)
        return ServerProxy(url)

    @api.one
    def _create_db(self):
        _logger.info('Creating database for %s...' % self.docker_container)
        branch = self.branch_id.branch_tmpl_id or self.branch_id
        sock_db = self._connect('db')
        params = [self.admin_passwd, DBNAME,
                  branch.install_demo_data, branch.lang, branch.user_passwd]
        if branch.country_id and LooseVersion(
                sock_db.server_version()[:3]) >= LooseVersion('9.0'):
            params += ['admin', branch.country_id.code]
        if LooseVersion(sock_db.server_version()[:3]) >= LooseVersion('6.1'):
            sock_db.create_database(*params)
        else:
            db_id = sock_db.create(*params)
            while True:
                progress = self.sock_db.get_progress(
                    self.admin_passwd, db_id)[0]
                if progress == 1.0:
                    break
                else:
                    time.sleep(1)

    @api.one
    def _restore_db(self):
        branch = self.branch_id.branch_tmpl_id or self.branch_id
        _logger.info('Restoring database for %s from file %s...' %
                     (self.docker_container, branch.dump_id.datas_fname))
        self._connect('db').restore(self.admin_passwd,
                                    DBNAME, branch.dump_id.datas)

    @api.one
    def _install_modules(self, modules_to_install):
        _logger.info('Installing modules %s for %s...' %
                     (modules_to_install, self.docker_container))
        branch = self.branch_id.branch_tmpl_id or self.branch_id
        sock_exec = partial(self._connect('object').execute,
                            DBNAME, branch.user_uid, branch.user_passwd)
        # Useful for restored database
        sock_exec('ir.module.module', 'update_list')
        module_ids_to_install = []
        for module_name in modules_to_install:
            module_ids = sock_exec('ir.module.module', 'search', [
                                   ('name', '=', module_name)], 0, 1)
            if not module_ids:
                raise UserError(_('Module %s does not exist') % module_name)
            module_ids_to_install.append(module_ids[0])
        try:
            sock_exec('ir.module.module', 'button_install',
                      module_ids_to_install)
            upgrade_id = sock_exec('base.module.upgrade', 'create', {})
            sock_exec('base.module.upgrade', 'upgrade_module', [upgrade_id])
        except Fault as f:
            msg = f.faultString
            if msg == 'None':
                msg = _('Check external dependencies')
            raise UserError(_('Error while modules installation\n\n%s' % msg))

    @api.one
    def _reactivate_admin(self):
        # INFO: since April 2015, logging as admin after smile_test execution
        # is not possible without reactivating it.
        _logger.info('Reactivate admin user for %s...' % self.docker_container)
        try:
            branch = self.branch_id.branch_tmpl_id or self.branch_id
            sock_exec = partial(self._connect('object').execute,
                                DBNAME, branch.user_uid, branch.user_passwd)
            sock_exec('res.users', 'write', branch.user_uid, {'active': True})
        except Exception:
            pass

    @api.one
    def _check_quality_code(self):
        _logger.info('Checking code quality for %s...' % self.docker_container)
        self._connect('common').check_quality_code(self.admin_passwd)

    @api.one
    def _count_lines_of_code(self):
        _logger.info('Counting lines of code for %s...' %
                     self.docker_container)
        self._connect('common').count_lines_of_code(self.admin_passwd)

    @api.one
    def _start_coverage(self):
        _logger.info('Starting code coverage for %s...' %
                     self.docker_container)
        self._connect('common').coverage_start(self.admin_passwd)

    @api.one
    def _stop_coverage(self):
        _logger.info('Stopping code coverage for %s...' %
                     self.docker_container)
        self._connect('common').coverage_stop(self.admin_passwd)

    @api.one
    def _run_tests(self):
        _logger.info('Running tests for %s...' % self.docker_container)
        self._connect('common').run_tests(self.admin_passwd, DBNAME)

    @api.one
    def _attach_files(self):
        _logger.info('Attaching files for %s...' % self.docker_container)
        branch = self.branch_id.branch_tmpl_id or self.branch_id
        container = self.docker_container
        filepaths = []
        for filename in [
                CONFIGFILE, COVERAGEFILE, LOGFILE, FLAKE8FILE, TESTFILE]:
            filepaths.append(os.path.join(branch.os_id.odoo_dir, filename))
        for path in branch.addons_path.replace(' ', '').split(','):
            filename = '%s.cloc' % path.split('/')[-1]
            filepaths.append(os.path.join(
                branch.os_id.odoo_dir, path, filename))
        missing_files = []
        for filepath in filepaths:
            filename = os.path.basename(filepath)
            filelike = None
            try:
                filelike = StringIO()
                for response in self.docker_host_id.get_archive(
                        container, filepath):
                    filelike.write(response)
                filelike.seek(0)
                tar = tarfile.open(fileobj=filelike)
                content = tar.extractfile(os.path.basename(filepath)).read()
                self.env['ir.attachment'].create({
                    'name': filename,
                    'datas_fname': filename,
                    'datas': base64.b64encode(content or ''),
                    'res_model': self._name,
                    'res_id': self.id,
                })
            except APIError:
                missing_files.append(filename)
            except Exception as e:
                _logger.error('Error while attaching %s: %s' %
                              (filename, get_exception_message(e)))
            finally:
                if filelike is not None:
                    filelike.close()
        if missing_files:
            _logger.info("The following files are missing: %s" % missing_files)

    @api.multi
    def _get_logs(self, filename):
        self.ensure_one()
        attachs = self.env['ir.attachment'].search([
            ('datas_fname', '=', filename),
            ('res_model', '=', self._name),
            ('res_id', '=', self.id),
        ], limit=1)
        return base64.b64decode(attachs and attachs[0].datas or '')

    @staticmethod
    def _is_flake8_error_code(code):
        return code[0] in ('E', 'F') or code == DEBUGGER_ERROR_CODE

    @staticmethod
    def _is_flake8_warning_code(code):
        return code[0] in ('W', 'C', 'N', 'T')

    @api.one
    def _load_flake8_logs(self):
        _logger.info('Parsing Flake8 logs for %s...' % self.docker_container)
        data = self._get_logs(FLAKE8FILE).split('\n')
        Log = self.env['scm.repository.branch.build.log']
        pattern = re.compile(
            r'([^:]+addons/)(?P<module>[^\/]*)(/)(?P<file>[^:]+):'
            r'(?P<line>\d*):(\d*): (?P<code>\w*) (?P<exception>[^$]*)')
        for line in data:
            m = pattern.match(line)
            if m:
                vals = m.groupdict()
                vals['build_id'] = self.id
                vals['type'] = 'quality_code'
                code = vals['code']
                if Build._is_flake8_error_code(code):
                    vals['result'] = 'error'
                elif Build._is_flake8_warning_code(code):
                    vals['result'] = 'warning'
                Log.create(vals)

    @api.one
    def _load_test_logs(self):
        _logger.info('Importing test logs for %s...' % self.docker_container)
        Log = self.env['scm.repository.branch.build.log']
        pattern = re.compile(r'([^:]+addons/)(?P<file>[^$]*)')
        csv_input = StringIO(self._get_logs(TESTFILE))
        reader = csv.DictReader(csv_input)
        for vals in reader:
            filepath = vals['file']
            if filepath:
                match = pattern.match(filepath)
                if match:
                    vals['file'] = match.groupdict()['file']
            vals['build_id'] = self.id
            vals['code'] = 'TEST'
            vals['type'] = 'test'
            vals['exception'] = tools.plaintext2html(vals['exception'])
            Log.create(vals)

    @api.one
    def _load_coverage_logs(self):
        _logger.info('Parsing coverage logs for %s...' % self.docker_container)
        Coverage = self.env['scm.repository.branch.build.coverage']
        pattern = re.compile(
            r'([^:]+addons/)(?P<module>[^\/]*)(/)(?P<file>[^$]*)')
        logs = self._get_logs(COVERAGEFILE)
        if not logs:
            return
        root = etree.fromstring(logs)
        for cls in root.xpath('//class'):
            vals = {}
            cls_info = dict(cls.items())
            match = pattern.match(cls_info['filename'])
            if not match:
                continue  # native code ignored
            infos = match.groupdict()
            vals['build_id'] = self.id
            vals['module'] = infos['module']
            vals['file'] = infos['file']
            vals['line_count'] = len(cls.find('lines').getchildren())
            vals['line_rate'] = float(cls_info['line-rate']) * 100
            vals['branch_count'] = len([c for c in cls.find(
                'lines').getchildren() if dict(c.items()).get('branch')])
            vals['branch_rate'] = float(cls_info['branch-rate']) * 100
            Coverage.create(vals)

    @api.one
    def _set_build_result(self):
        if self.result in ('failed', 'killed'):
            return
        _logger.info('Getting the result for %s...' % self.docker_container)
        lines_count = sum(
            [coverage.line_count for coverage in self.coverage_ids])
        covered_lines_count = sum(
            [coverage.line_rate * coverage.line_count
             for coverage in self.coverage_ids])
        self.write({
            'quality_code_count': len(self.log_ids.filtered(
                lambda log: log.type == 'quality_code' and
                log.result == 'error')),
            'failed_test_count': len(self.log_ids.filtered(
                lambda log: log.type == 'test' and log.result == 'error')),
            'test_count': len(self.log_ids.filtered(
                lambda log: log.type == 'test' and log.result != 'ignored')),
            'coverage_avg':
                lines_count and covered_lines_count / lines_count or 0.0,
            'result': self.log_ids.filtered(
                lambda log: log.result == 'error') and 'unstable' or 'stable',
        })
        if self.result == 'stable':
            previous_build = self.search([
                ('branch_id', '=', self.branch_id.id),
                ('id', '<', self.id),
                ('state', 'in', ('running', 'done')),
                ('result', 'in', ('failed', 'unstable', 'stable')),
            ], limit=1, order='id desc')
            if previous_build.result != 'stable':
                self._send_build_result('Back to stable')
        elif self.result == 'unstable':
            self._send_build_result('Unstable')

    @api.one
    def _send_build_result(self, short_message):
        "Send build result and error message to branch followers"
        _logger.debug('Sending email for %s...' % self.docker_container)
        context = {
            'subject': short_message,
            'build_url': self._get_action_url(**{
                'res_id': self.id, 'model': self._name, 'view_type': 'form',
                'action_id': self.env.ref(
                    'smile_ci.action_repository_branch_build').id,
            }),
        }
        if self.commit_logs:
            context['commit_logs'] = tools.plaintext2html(self.commit_logs)
        if 'build_error' in self._context:
            context['build_error'] = tools.plaintext2html(
                self._context['build_error'])
        branch_subtype_id = self.env.ref(
            'smile_ci.subtype_build_result').id
        repository_subtype_id = self.env.ref(
            'smile_ci.subtype_build_result2').id
        context['partner_to_notify'] = self.branch_id.get_partners_to_notify(
            branch_subtype_id, repository_subtype_id)
        self = self.with_context(**context)
        template = self.env.ref('smile_ci.mail_template_build_result')
        self.message_post_with_template(template.id)
        self._notify_slack()

    @api.one
    def _notify_slack(self):
        if self.branch_id.slack_integration and self.branch_id.slack_webhook:
            _logger.debug('Sending Slack notification for %s...'
                          % self.docker_container)
            payload = {
                'text': self._get_slack_message(),
                'attachments': self._get_slack_attachments(),
            }
            icon_emoji = self._get_slack_icon_emoji()
            if self.branch_id.slack_webhook.startswith(
                    'https://hooks.slack.com/services'):  # Slack case
                payload['icon_emoji'] = icon_emoji
            else:  # Mattermost case
                payload['text'] = '{} {}'.format(icon_emoji, payload['text'])
            if self.branch_id.slack_channel:
                payload['channel'] = self.branch_id.slack_channel
            if self.branch_id.slack_username:
                payload['username'] = self.branch_id.slack_username
            try:
                requests.post(self.branch_id.slack_webhook,
                              data=json.dumps(payload))
            except Exception as e:
                _logger.error('Slack Integration Error on the branch %s: %s' %
                              (self.branch_id.display_name, e))

    @api.multi
    def _get_slack_message(self):
        self.ensure_one()
        return '%(branch_name)s %(branch_branch)s - ' \
               '<%(build_url)s|Build %(build_id)s> - %(subject)s' % {
                   'branch_name': self.branch_id.name,
                   'branch_branch': self.branch_id.branch,
                   'build_url': self._context['build_url'],
                   'build_id': self.id,
                   'subject': self._context["subject"],
               }

    @api.multi
    def _get_slack_attachments(self):
        self.ensure_one()
        attachments = []
        if self.result == 'failed':
            attachments.append({
                'fallback': self._context["subject"],
                'color': 'danger',
                'fields': [{
                    "title": _("Error"),
                    "value": self._context["build_error"],
                    "short": False,
                }],
            })
        else:
            attachments.append({
                "fallback": self._context["subject"],
                "color": 'good' if self.result == "stable" else 'warning',
                "fields": [{
                    "title": _("Failed tests"),
                    "value": self.failed_test_ratio,
                    "short": True,
                }, {
                    "title": _("Coverage average"),
                    "value": "%.2f%%" % self.coverage_avg,
                    "short": True,
                }, {
                    "title": _("Quality errors"),
                    "value": self.quality_code_count,
                    "short": True,
                }],
            })
        return attachments

    @api.multi
    def _get_slack_icon_emoji(self):
        self.ensure_one()
        if self.result == 'failed':
            return ':sob:'
        if self.result == "stable":
            return ":relieved:"
        return ":confused:"

    @api.one
    def _load_logs_in_db(self):
        for log_type in ('test', 'flake8', 'coverage'):
            try:
                getattr(self, '_load_%s_logs' % log_type)()
            except Exception as e:
                _logger.error('Error while loading %s logs: %s' %
                              (log_type, get_exception_message(e)))

    @api.one
    def _generate_tests_report(self):
        try:
            tests_by_module = self._connect(
                'common').list_tests(self.admin_passwd, DBNAME)
            Report = self.env['report'].sudo().with_context(
                tests_by_module=tests_by_module)
            content = Report.get_pdf(self.ids, 'smile_ci.report_tests')
            filename = 'report_tests.pdf'
            self.env['ir.attachment'].create({
                'name': filename,
                'datas_fname': filename,
                'datas': base64.b64encode(content or ''),
                'res_model': self._name,
                'res_id': self.id,
            })
        except Exception as e:
            _logger.error('Error while generating tests report: %s' %
                          (get_exception_message(e)))

    @api.multi
    def remove_container(self, ignore_exceptions=True):
        try:
            return super(Build, self).remove_container(remove_image=True)
        except Exception as e:
            msg = tools.ustr(e)
            if ignore_exceptions:
                _logger.error(msg)
                return True
            raise UserError(msg)

    @api.multi
    def unlink(self):
        if self.filtered(lambda build: build.state == 'testing' and
                         not build.is_killable):
            raise UserError(
                _('You cannot delete a non-killable testing build'))
        self.remove_container()
        return super(Build, self).unlink()

    @api.one
    def _kill_container(self, ignore_exceptions=True):
        vals = {'state': 'done', 'port': False, 'is_to_keep': False}
        if self.state != 'running':
            vals['result'] = 'killed'
        self.write_with_new_cursor(vals)
        if self.state != 'pending':
            self.remove_container(ignore_exceptions)

    @api.multi
    def kill_container(self):
        self.ensure_one()
        _logger.info('Build %s was killed by user %d (%s)...' %
                     (self.id, self._uid, self.env.user.name))
        if self.filtered(lambda build: not build.is_killable):
            raise UserError(
                _("You can't kill a build "
                  "if its container has not been started!"))
        self._kill_container(ignore_exceptions=False)
        return True

    @api.multi
    def keep_alive(self):
        "Toogle state of build"
        self.ensure_one()
        self.is_to_keep = not self.is_to_keep

    @api.multi
    def open(self):
        self.ensure_one()
        return {
            'name': _('Open URL'),
            'type': 'ir.actions.act_url',
            'url': self.url,
            'target': 'new',
        }

    @api.model
    def purge(self, date):
        builds = self.search([('create_date', '<=', date)])
        return builds.unlink()

    @api.multi
    def start_container_from_registry(self):
        self.ensure_one()
        docker_host_id = self._get_default_docker_host()
        port = self.env['docker.host'].browse(
            docker_host_id).find_ports().pop()
        self.write_with_new_cursor({
            'docker_host_id': docker_host_id,
            'port': port,
        })
        super(Build, self).start_container_from_registry(
            # tag=self.result,
            # The previous line has been commented since we gave up
            # tagging the images to store in registry
            ports=['%s:8069' % port])
        return self.write_with_new_cursor({'state': 'running'})

    # Logs

    @api.multi
    def show_logs(self):
        "Get logs from Docker and show them inside a pop-up."
        self.ensure_one()
        view = self.env.ref('smile_ci.view_build_show_server_logs')
        return self.open_wizard(name='Server logs', view_id=view.id)

    @api.model
    def _get_purge_date(self, age_number, age_type):
        assert isinstance(age_number, (int, long))
        assert age_type in ('years', 'months', 'weeks',
                            'days', 'hours', 'minutes', 'seconds')
        date = fields.Datetime.from_string(
            fields.Datetime.now()) + relativedelta(**{age_type: -age_number})
        return fields.Date.to_string(date)

    @api.model
    def purge_logs(self, age_number=1, age_type='months'):
        date = self._get_purge_date(age_number, age_type)
        _logger.info('Purging logs created before %s...' % (date,))
        self.env['scm.repository.branch.build.log'].purge(date)
        self.env['scm.repository.branch.build.coverage'].purge(date)
        return True

    # Dashboard

    @api.model
    def read_group(self, domain, fields, groupby, offset=0, limit=None,
                   orderby=False, lazy=True):
        result = super(Build, self).read_group(
            domain, fields, groupby, offset, limit, orderby, lazy)
        if not orderby and groupby == ['branch_id']:
            return sorted(result, key=lambda res: res['branch_id'][1])
        return result

    # Cleaning

    @api.model
    def _remove_not_pending_build_directories(self):
        # Remove build directories except for pending builds
        directories = self.search(
            [('state', '=', 'pending')]).mapped('build_directory')
        builds_path = self.env['docker.host'].builds_path
        for dirname in os.listdir(builds_path):
            dirpath = os.path.join(builds_path, dirname)
            if dirname.startswith('build_') and dirpath not in directories or \
                    dirname.startswith('branch_'):
                _logger.info('Removing %s' % dirpath)
                thread = Thread(target=shutil.rmtree, args=(dirpath,))
                thread.start()

    @api.model
    def _recreate_testing_builds(self):
        # Kill testing builds
        testing_builds = self.search([('state', '=', 'testing')])
        branches_to_force = testing_builds.mapped('branch_id')
        if testing_builds:
            _logger.info('Killing testing builds %s' % str(testing_builds.ids))
            testing_builds._kill_container()
        # Force build creation for branch in test
        if branches_to_force:
            _logger.info('Force build creation for branches %s' %
                         str(branches_to_force.ids))
            branches_to_force = branches_to_force.with_context(
                in_new_thread=True)
            thread = Thread(
                target=branches_to_force.create_builds, args=(True,))
            thread.start()

    @api.model
    def _kill_not_really_running_builds(self):
        # Kill running builds with not running containers
        real_running_build_ids = set()
        for docker_host in self.env['docker.host'].search([]):
            for container in docker_host.get_containers(all=True):
                for name in container['Names']:
                    if name.startswith('/build_'):
                        build_id = int(name.replace(
                            '/build_', '').split('/')[0])
                        try:
                            if container['State'] in ('created', 'exited'):
                                docker_host.start_container(container['Id'])
                        except Exception:
                            break
                        else:
                            real_running_build_ids.add(build_id)
        virtual_running_build_ids = set(
            self.search([('state', '=', 'running')]).ids)
        builds_to_kill = virtual_running_build_ids - real_running_build_ids
        if builds_to_kill:
            _logger.info('Killing running builds %s' % builds_to_kill)
            builds_to_kill = self.browse(list(builds_to_kill))
            builds_to_kill._kill_container()

    @api.model
    def _remove_unknown_containers(self):
        real_running_build_ids = []
        for docker_host in self.env['docker.host'].search([]):
            for container in docker_host.get_containers(all=True):
                for name in container['Names']:
                    try:
                        build_id = int(name.split('_')[-1])
                        real_running_build_ids.append(build_id)
                    except Exception:
                        pass
        real_running_builds = self.search(
            [('id', 'in', real_running_build_ids)])
        virtual_running_builds = self.search(
            [('state', '=', 'running')])
        containers_to_kill = set(real_running_builds.ids) - \
            set(virtual_running_builds.ids)
        if containers_to_kill:
            _logger.info('Killing running containers %s' % containers_to_kill)
            for docker_host in self.env['docker.host'].search([]):
                for container in docker_host.get_containers(all=True):
                    for name in container['Names']:
                        try:
                            build_id = int(name.split('_')[-1])
                        except Exception:
                            build_id = False
                        if build_id in containers_to_kill:
                            try:
                                docker_host.remove_container(
                                    name.replace('/', ''), force=True)
                            except Exception as e:
                                _logger.error(e)

    @api.model
    def _clean_networks(self):
        # Try to remove all networks
        for docker_host in self.env['docker.host'].search([]):
            docker_host.clean_networks()

    @api.model
    def init(self):
        super(Build, self).init()
        callers = [frame[3] for frame in inspect.stack()]
        if 'preload_registries' in callers:
            try:
                _logger.info(
                    "Cleaning testing/running builds before restarting")
                self._remove_not_pending_build_directories()
                self._recreate_testing_builds()
                self._kill_not_really_running_builds()
                self._remove_unknown_containers()
                self._clean_networks()
            except Exception as e:
                _logger.error(get_exception_message(e))
