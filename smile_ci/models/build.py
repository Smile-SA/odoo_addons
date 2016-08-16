# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2014 Smile (<http://www.smile.fr>).
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

import base64
import cStringIO
import csv
from datetime import datetime
from dateutil.relativedelta import relativedelta
from functools import partial
import logging
from lxml import etree
import os
import psutil
import re
import shutil
import StringIO
import tarfile
import tempfile
from threading import Lock, Thread
import time
from urlparse import urljoin, urlparse
import xmlrpclib

from openerp import api, models, fields, SUPERUSER_ID, tools, _
from openerp.exceptions import Warning
from openerp.modules.registry import Registry
import openerp.modules as addons
from openerp.tools import config
from openerp.tools import DEFAULT_SERVER_DATETIME_FORMAT as DATETIME_FORMAT
from openerp.tools.safe_eval import safe_eval as eval

from openerp.addons.smile_scm.tools import cd

from ..tools import cursor, with_new_cursor, s2human, mergetree, get_exception_message

_logger = logging.getLogger(__package__)

try:
    from docker.errors import APIError
except ImportError:
    _logger.warning("Please install docker package")

try:
    import flake8_debugger
except ImportError:
    _logger.warning("Please install flake8-debugger package")

try:
    import flake8_print
except ImportError:
    _logger.warning("Please install flake8-print package")

BUILD_RESULTS = [
    ('stable', 'Stable'),
    ('unstable', 'Unstable'),
    ('failed', 'Failed'),
    ('killed', 'Killed'),
]
IGNORE_PATTERNS = ['.svn', '.git', '.bzr', '.hg', '*.pyc', '*.pyo', '*~', '~*']
DBNAME = 'test'
CONFIGFILE = 'server.conf'
COVERAGEFILE = 'coverage.xml'
DOCKERFILE = 'Dockerfile'
FLAKE8FILE = 'flake8.log'
LOGFILE = 'server.log'
TESTFILE = 'scm.repository.branch.build.log.csv'
TEST_MODULE = 'smile_test'
TODO_ERROR_CODE = 'T000'


def state_cleaner(method):
    def new_load(self, cr, *args, **kwargs):
        res = method(self, cr, *args, **kwargs)
        try:
            build_obj = self.get('scm.repository.branch.build')
            if build_obj:
                cr.execute("select relname from pg_class where relname='%s'" % build_obj._table)
                if cr.rowcount:
                    _logger.info("Cleaning testing/running builds before restarting")
                    # Empty builds directory: sources being copied when killing the server are not deleted
                    for dirname in os.listdir(build_obj._builds_path):
                        Thread(target=shutil.rmtree, args=(os.path.join(build_obj._builds_path, dirname),)).start()
                    # Search testing builds
                    build_infos = build_obj.search_read(cr, SUPERUSER_ID, [('state', '=', 'testing')], ['ppid'])
                    build_ids = [b['id'] for b in build_infos if not psutil.pid_exists(b['ppid'])]
                    branch_ids = [b['branch_id'] for b in build_obj.read(cr, SUPERUSER_ID, build_ids, ['branch_id'], load='_classic_write')]
                    if build_ids:
                        # Kill invalid builds
                        build_obj._remove_container(cr, SUPERUSER_ID, build_ids)
                        build_obj.write(cr, SUPERUSER_ID, build_ids, {'state': 'done', 'result': 'killed'})
                    # Search running builds not running anymore
                    runnning_build_ids = build_obj.search(cr, SUPERUSER_ID, [('state', '=', 'running')])
                    actual_runnning_build_ids = []
                    docker_host_obj = self['docker.host']
                    for docker_host_id in docker_host_obj.search(cr, SUPERUSER_ID, []):
                        docker_host = docker_host_obj.browse(cr, SUPERUSER_ID, docker_host_id)
                        actual_runnning_build_ids += [int(container['Names'][0].replace('/build_', ''))
                                                      for container in docker_host.get_client().containers()
                                                      if container['Names'] and container['Names'][0].startswith('/build_')]
                    build_ids = list(set(runnning_build_ids) - set(actual_runnning_build_ids))
                    if build_ids:
                        # Kill invalid builds
                        build_obj._remove_container(cr, SUPERUSER_ID, build_ids)
                        build_obj.write(cr, SUPERUSER_ID, build_ids, {'state': 'done'})
                    # Force build creation for branch in test before server stop
                    if branch_ids:
                        branch_obj = self.get('scm.repository.branch')
                        thread = Thread(target=branch_obj._force_create_build_with_new_cursor, args=(branch_ids,))
                        thread.start()
        except Exception, e:
            _logger.error(get_exception_message(e))
        return res
    return new_load


class Build(models.Model):
    _name = 'scm.repository.branch.build'
    _description = 'Build'
    _inherit = ['mail.thread']
    _rec_name = 'id'
    _order = 'id desc'

    def __init__(self, pool, cr):
        cls = type(self)
        cls._scheduler_lock = Lock()
        super(Build, self).__init__(pool, cr)
        setattr(Registry, 'setup_models', state_cleaner(getattr(Registry, 'setup_models')))

    def _get_url(self):
        netloc = urlparse(self.host).netloc
        if self.docker_host_id.redirect_subdomain_to_port:
            # Add subdomain build_%(port)s
            if netloc.startswith('www.'):
                netloc.replace('www.', '')
            return urljoin(self.host, '//build_%s.%s' % (self.port, netloc))
        # Replace default port by build port
        netloc = netloc.split(':')[0]
        return urljoin(self.host, '//%s:%s' % (netloc, self.port))

    @api.one
    @api.depends('docker_host_id', 'port')
    def _compute_url(self):
        self.url = self._get_url()

    @api.one
    @api.depends('date_start')
    def _get_time(self):
        if not self.date_start or (not self.date_stop and self.state in ('running', 'done')):
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
            timedelta = datetime.now() - fields.Datetime.from_string(self.date_start)
            self.age = timedelta.total_seconds()

    @api.one
    def _convert_time_to_human(self):
        self.time_human = s2human(self.time)

    @api.one
    def _convert_age_to_human(self):
        self.age_human = s2human(self.age)

    @api.one
    def _get_last_build_time_human(self):
        last_builds = self.branch_id.build_ids.filtered(lambda build: build.result in ('unstable', 'stable') and build.id < self.id)
        self.last_build_time_human = last_builds[0].time_human if last_builds else ''

    @api.model
    def _get_default_docker_host(self):
        docker_hosts = self.env['docker.host'].search([])
        if not docker_hosts:
            raise Warning(_('No docker host is configured'))
        # TODO: loads balance over each docker host
        return docker_hosts[0].id

    @api.one
    def _get_failed_test_ratio(self):
        self.failed_test_ratio = '%s / %s' % (self.failed_test_count, self.test_count)

    @api.one
    def _get_last_server_logs(self):
        limit = self._context.get('limit', 20)
        if type(limit) == str:
            limit = int(limit)
        cli = self._docker_cli
        logs = []
        for line in cli.copy(self._get_container_name(), os.path.join(self.branch_id.os_id.odoo_dir, LOGFILE)):
            logs.append(line)
        self.server_logs = ''.join(logs[-limit:])

    id = fields.Integer('Number', readonly=True)
    branch_id = fields.Many2one('scm.repository.branch', 'Branch', required=True, readonly=True, index=True, ondelete='cascade')
    revno = fields.Char('Revision', required=True, readonly=True)
    commit_logs = fields.Text('Last commits', readonly=True)
    create_uid = fields.Many2one('res.users', 'User', readonly=True)
    create_date = fields.Datetime('Date', readonly=True)
    state = fields.Selection([
        ('pending', 'Pending'),
        ('testing', 'Testing'),
        ('running', 'Running'),
        ('done', 'Done'),
    ], 'State', readonly=True, default='pending')
    result = fields.Selection(BUILD_RESULTS, 'Result', readonly=True)
    directory = fields.Char(readonly=True)
    docker_host_id = fields.Many2one('docker.host', readonly=True, default=_get_default_docker_host)
    host = fields.Char(related='docker_host_id.build_base_url', readonly=True)
    port = fields.Char(readonly=True)
    url = fields.Char(compute='_compute_url')
    date_start = fields.Datetime('Start date', readonly=True)
    date_stop = fields.Datetime('End date', readonly=True)
    time = fields.Integer(compute='_get_time')
    age = fields.Integer(compute='_get_age')
    time_human = fields.Char('Time', compute='_convert_time_to_human', store=False)
    age_human = fields.Char('Age', compute='_convert_age_to_human', store=False)
    last_build_time_human = fields.Char('Last build time', compute='_get_last_build_time_human', store=False)
    log_ids = fields.One2many('scm.repository.branch.build.log', 'build_id', 'Logs', readonly=True)
    coverage_ids = fields.One2many('scm.repository.branch.build.coverage', 'build_id', 'Coverage', readonly=True)
    quality_code_count = fields.Integer('# Quality errors', readonly=True)
    failed_test_count = fields.Integer('# Failed tests', readonly=True)
    test_count = fields.Integer('# Tests', readonly=True)
    failed_test_ratio = fields.Char('Failed tests ratio', compute='_get_failed_test_ratio')
    coverage_avg = fields.Float('Coverage average', readonly=True, group_operator='avg')
    ppid = fields.Integer('Launcher Process Id', readonly=True)
    is_to_keep = fields.Boolean("Keep alive", readonly=True, help="If checked, this build will not be stopped by scheduler")
    is_killable = fields.Boolean("Can be killed", readonly=True, help="A build can only be killed if its container is started")
    server_logs = fields.Text(compute='_get_last_server_logs', context={'limit': 30})

    @property
    def _docker_cli(self):
        return self.docker_host_id.get_client()

    @property
    def _builds_path(self):
        builds_path = config.get('builds_path') or tempfile.gettempdir()
        if not os.path.isdir(builds_path):
            raise Warning(_("%s doesn't exist or is not a directory") % builds_path)
        return builds_path

    @api.model
    def create(self, vals):
        build = super(Build, self.with_context(mail_create_nosubscribe=True)).create(vals)
        build._copy_sources()
        return build

    @staticmethod
    def _get_branches_to_merge(branch):
        """
        Compute first level dependencies of a branch and returns a list of tuple (Branch, subfolder).

        @param branch: Branch
        @return: list
        """
        branches = [(branch, branch.subfolder or '')]
        for dependency in branch.branch_dependency_ids:
            branches.append((dependency.merge_with_branch_id, dependency.merge_subfolder or ''))
        return branches[::-1]

    @api.one
    def _copy_sources(self):
        _logger.info('Copying %s %s sources...' % (self.branch_id.name, self.branch_id.branch))
        try:
            self.directory = os.path.join(self._builds_path, str(self.id))
            ignore_patterns = shutil.ignore_patterns(TEST_MODULE, *IGNORE_PATTERNS)  # Do not copy smile_test and useless files
            for branch, subfolder in Build._get_branches_to_merge(self.branch_id):
                mergetree(branch.directory, os.path.join(self.directory, subfolder), ignore_patterns)
            self._add_ci_addons()
        except Exception, e:
            msg = get_exception_message(e)
            _logger.error(msg)
            self._remove_directory()
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
        with cd(self.directory):
            shutil.copytree(ci_addons_path, 'ci-addons', ignore=ignore_patterns)

    def write_with_new_cursor(self, vals):
        with cursor(self._cr.dbname, False) as new_cr:
            return self.with_env(self.env(cr=new_cr)).write(vals)

    @api.model
    def scheduler(self):
        with self._scheduler_lock:
            self._scheduler()
        return True

    @api.model
    def _scheduler(self):
        testing = self.search_count([('state', '=', 'testing')])
        max_testing = int(self.env['ir.config_parameter'].get_param('ci.max_testing'))
        max_testing_by_branch = int(self.env['ir.config_parameter'].get_param('ci.max_testing_by_branch'))
        builds_to_run = self.search([('branch_id.use_in_ci', '=', True),
                                     ('state', '=', 'pending')], order='id asc')
        if builds_to_run:
            ports = sorted(self._find_ports(), reverse=True)
            builds_in_test = self.search([('branch_id.use_in_ci', '=', True),
                                          ('state', '=', 'testing')], order='id asc')
        for build in builds_to_run:
            # Check max_testing_by_branch
            builds_by_branch = [b for b in builds_in_test if b.branch_id == build.branch_id]
            if len(builds_by_branch) >= max_testing_by_branch:
                continue
            # Check max_testing
            testing += 1
            if testing > max_testing:
                break
            # Use a new cursor to avoid concurrent update if loop is longer than build test
            build.write_with_new_cursor({
                'state': 'testing',
                'result': '',
                'date_start': fields.Datetime.now(),
                'port': ports.pop(),
                'ppid': os.getpid(),
            })
            # Use a new thread in order to launch other build tests without waiting the end of the first one
            new_thread = Thread(target=self._test_in_new_thread, args=(build,))
            new_thread.start()
            time.sleep(0.1)  # ?!!

    @api.model
    def image_exists_in_registry(self):
        # TODO: implements me
        # check if self._get_image_name() exists in Docker registry
        return False

    @api.model
    def _test_in_new_thread(self, build):
        with api.Environment.manage():
            return self.browse(build)._test()

    @api.multi
    @with_new_cursor(False)
    def _test(self):
        self.ensure_one()
        _logger.info('Testing build %s...' % self.id)
        try:
            if not self.image_exists_in_registry():
                self._create_configfile()
                self._create_dockerfile()
                self._build_image()
                self._remove_directory()
            self._run_container()
            time.sleep(5)  # Ensure that Odoo is launched before calling services
            self._check_quality_code()
            self._count_lines_of_code()
            self._start_coverage()
            if self.branch_id.dump_id:
                self._restore_db()
            else:
                self._create_db()
            if self.branch_id.modules_to_install:
                modules_to_install = self.branch_id.modules_to_install.replace(' ', '').split(',')
                self._install_modules(modules_to_install)
            self._run_tests()
            self._stop_coverage()
            self._reactivate_admin()
        except IOError, e:
            _logger.info('Build %s was killed...' % self.id)
            _logger.error('IOError infos: %s' % str(e))
            self = self.with_context(killed=True)  # pass killed through context to not send result by email
        except Exception, e:
            self.write_with_new_cursor({'state': 'done', 'result': 'failed', 'date_stop': fields.Datetime.now()})
            msg = get_exception_message(e)
            _logger.error(msg)
            self.with_context(build_error=msg)._send_build_result('Failed')
            self._remove_directory()
        else:
            self.write_with_new_cursor({'state': 'running', 'date_stop': fields.Datetime.now()})
        finally:
            self._attach_files()
            self._load_logs_in_db()
            self._set_build_result()
            self._check_running()
            if self.result == 'failed':
                self._remove_physical_container()

    @api.model
    def _check_max_running(self, domain, param):
        running = self.search(domain, order='date_start desc')
        max_running = int(self.env['ir.config_parameter'].get_param(param))
        if len(running) > max_running:
            running_to_keep = running.filtered(lambda build: build.is_to_keep)
            max_running = max(max_running - len(running_to_keep), 0)
            running_not_to_keep = running - running_to_keep
            running_not_to_keep[max_running:]._remove_container()

    @api.one
    def _check_running(self):
        if not self.branch_id.version_id.web_included:
            self._remove_container()
        # Check max_running_by_branch
        self._check_max_running(domain=[('state', '=', 'running'), ('branch_id', '=', self.branch_id.id)], param='ci.max_running_by_branch')
        # Check max_running
        self._check_max_running(domain=[('state', '=', 'running')], param='ci.max_running')

    @property
    def admin_passwd(self):
        return self.env['ir.config_parameter'].get_param('ci.admin_passwd')

    def _get_options(self):
        branch = self.branch_id

        def format_str(path):
            if not path:
                return path
            path = path[:]  # To avoid to update database when call replace method - A behaviour caused by new api
            return ','.join(map(lambda p: os.path.join(branch.os_id.odoo_dir, p),
                                path.replace(' ', '').split(',')))

        return {
            'db_user': 'odoo',
            'db_password': 'odoo',
            'db_name': False,
            'logfile': format_str(LOGFILE),
            'coveragefile': format_str(COVERAGEFILE),
            'flake8file': format_str(FLAKE8FILE),
            'flake8_exclude_files': self.env['ir.config_parameter'].get_param('ci.flake8.exclude_files'),
            'flake8_max_line_length': self.env['ir.config_parameter'].get_param('ci.flake8.max_line_length'),
            'code_path': format_str(self.branch_id.code_path),
            'test_path': format_str(','.join([branch.test_path or '', 'ci-addons'])),
            'addons_path': format_str(','.join([branch.addons_path or '', 'ci-addons'])),
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
        _logger.info('Generating %s for build:%s...' % (CONFIGFILE, self.id))
        options = self._get_options()
        with cd(self.directory):
            with open(CONFIGFILE, 'w') as cfile:
                cfile.write('[options]\n')
                for k, v in options.iteritems():
                    cfile.write('%s = %s\n' % (k, v))
                if self.branch_id.additional_options:
                    cfile.write(self.branch_id.additional_options)

    @api.one
    def _create_dockerfile(self):
        _logger.info('Generating dockerfile for build:%s...' % self.id)
        content = base64.b64decode(self.branch_id.os_id.dockerfile)
        package = self.branch_id.version_id.package_ids.filtered(lambda package: package.os_id == self.branch_id.os_id)
        localdict = {
            'required_packages': package.required_packages or '',
            'optional_packages': package.optional_packages or '',
            'specific_packages': self.branch_id.specific_packages or '',
            'pip_packages': self.branch_id.pip_packages or '',
            'flake_8_packages': self.env['ir.config_parameter'].get_param('ci.flake8.extensions'),
            'configfile': CONFIGFILE,
            'server_cmd': os.path.join(self.branch_id.server_path,
                                       self.branch_id.version_id.server_cmd),
            'odoo_dir': self.branch_id.os_id.odoo_dir,
        }
        with cd(self.directory):
            with open(DOCKERFILE, 'w') as f:
                f.write(content % localdict)

    @api.multi
    def _get_image_name(self):
        self.ensure_one()
        return 'build:%s' % self.id

    @api.multi
    def _get_container_name(self):
        self.ensure_one()
        return 'build_%s' % self.id

    @api.multi
    def _get_build_params(self):
        self.ensure_one()
        return {
            'path': self.directory,
            'tag': self._get_image_name(),
            'rm': True,
        }

    @api.multi
    def _get_create_container_params(self):
        self.ensure_one()
        return {
            'image': self._get_image_name(),
            'name': self._get_container_name(),
            'detach': True,
            'ports': [8069]
        }

    @api.multi
    def _get_start_params(self):
        self.ensure_one()
        return {
            'port_bindings': {8069: int(self.port)},
        }

    @api.one
    def _build_image(self):
        _logger.info('Building image build:%s...' % self.id)
        # TODO: copy sources in a tar archive and use it as fileobj with custom_context=True
        params = self._get_build_params()
        _logger.debug(repr(params))
        generator = self._docker_cli.build(**params)
        all_lines = []
        for line in generator:
            all_lines.append(eval(line.replace('\n', '')))
            _logger.debug(line)
        if 'Successfully built' not in all_lines[-1].get('stream', ''):
            raise Exception(repr(all_lines[-1]['error']))

    @api.one
    def _run_container(self):
        _logger.info('Running container build_%s and expose it in port %s...' % (self.id, self.port))
        params = self._get_create_container_params()
        _logger.debug(repr(params))
        container = self._docker_cli.create_container(**params)
        params = self._get_start_params()
        _logger.debug(repr(params))
        self._docker_cli.start(container, **params)
        try:
            self._check_if_running()
        except:
            self.write_with_new_cursor({'state': 'done', 'result': 'killed'})
            raise
        self.write_with_new_cursor({'is_killable': True})

    @api.one
    def _check_if_running(self):
        t0 = time.time()
        sock_db = self._connect('db')
        while True:
            try:
                sock_db.server_version()
                break
            except:
                if time.time() - t0 >= 60:
                    _logger.error('Container build_%s exposed on port %s is not answering...' % (self.id, self.port))
                    raise

    @api.model
    def _find_ports(self):
        _logger.info('Searching available ports...')
        range_args = map(int, self.env['ir.config_parameter'].get_param('ci.port_range').split(','))
        available_ports = set(range(*range_args))
        build_infos = self.search_read([('state', 'in', ('testing', 'running'))], ['port'])
        busy_ports = {int(b['port']) for b in build_infos if b['port']}
        available_ports -= busy_ports
        if not available_ports:
            raise Warning(_('No available ports'))
        return available_ports

    @api.multi
    def _connect(self, service):
        self.ensure_one()
        xmlrpc = 'xmlrpc'
        if self.branch_id.version_id.standard_xmlrpc:
            xmlrpc = 'xmlrpc/2'
        url = '%s/%s/%s' % (self._get_url(), xmlrpc, service)
        return xmlrpclib.ServerProxy(url)

    @api.one
    def _create_db(self):
        _logger.info('Creating database for build_%s...' % self.id)
        branch = self.branch_id
        sock_db = self._connect('db')
        if sock_db.server_version()[:3] >= '6.1':
            sock_db.create_database(self.admin_passwd, DBNAME, branch.install_demo_data, branch.lang, branch.user_passwd)
        else:
            db_id = sock_db.create(self.admin_passwd, DBNAME, branch.install_demo_data, branch.lang, branch.user_passwd)
            while True:
                progress = self.sock_db.get_progress(self.admin_passwd, db_id)[0]
                if progress == 1.0:
                    break
                else:
                    time.sleep(1)

    @api.one
    def _restore_db(self):
        _logger.info('Restoring database for build_%s from file %s...' % (self.id, self.branch_id.dump_id.datas_fname))
        sock_db = self._connect('db')
        dump_file = self.branch_id.dump_id.datas
        sock_db.restore(self.admin_passwd, DBNAME, dump_file)

    @api.one
    def _install_modules(self, modules_to_install):
        _logger.info('Installing modules %s for build_%s...' % (modules_to_install, self.id))
        branch = self.branch_id
        sock_object = self._connect('object')
        sock_exec = partial(sock_object.execute, DBNAME, branch.user_uid, branch.user_passwd)
        sock_exec('ir.module.module', 'update_list')  # Useful for restored database
        module_ids_to_install = []
        for module_name in modules_to_install:
            module_ids = sock_exec('ir.module.module', 'search', [('name', '=', module_name)], 0, 1)
            if not module_ids:
                raise Exception('Module %s does not exist' % module_name)
            module_ids_to_install.append(module_ids[0])
        try:
            sock_exec('ir.module.module', 'button_install', module_ids_to_install)
            upgrade_id = sock_exec('base.module.upgrade', 'create', {})
            sock_exec('base.module.upgrade', 'upgrade_module', [upgrade_id])
        except xmlrpclib.Fault, f:
            _logger.debug('Error while modules installation for build %s:\n%s' % (self.id, f))
            raise Exception(f.faultString)

    @api.one
    def _reactivate_admin(self):
        # INFO: since April 2015, logging as admin after smile_test execution is not possible
        # without reactivating it.
        _logger.info('Reactivate admin user for build_%s...' % self.id)
        branch = self.branch_id
        sock_object = self._connect('object')
        sock_exec = partial(sock_object.execute, DBNAME, branch.user_uid, branch.user_passwd)
        admin_uid = 1
        sock_exec('res.users', 'write', admin_uid, {'active': True})

    @api.one
    def _check_quality_code(self):
        _logger.info('Checking quality code for build_%s...' % self.id)
        self._connect('common').check_quality_code(self.admin_passwd)

    @api.one
    def _count_lines_of_code(self):
        _logger.info('Counting lines of code for build_%s...' % self.id)
        self._connect('common').count_lines_of_code(self.admin_passwd)

    @api.one
    def _start_coverage(self):
        _logger.info('Starting code coverage for build_%s...' % self.id)
        self._connect('common').coverage_start(self.admin_passwd)

    @api.one
    def _stop_coverage(self):
        _logger.info('Stopping code coverage for build_%s...' % self.id)
        self._connect('common').coverage_stop(self.admin_passwd)

    @api.one
    def _run_tests(self):
        _logger.info('Running tests for build_%s...' % self.id)
        self._connect('common').run_tests(self.admin_passwd, DBNAME)

    @api.one
    def _attach_files(self):
        _logger.info('Attaching files for build_%s...' % self.id)
        container = self._get_container_name()
        filepaths = []
        for filename in [CONFIGFILE, COVERAGEFILE, DOCKERFILE, LOGFILE, FLAKE8FILE, TESTFILE]:
            import pdb; pdb.set_trace()
            filepaths.append(os.path.join(self.branch_id.os_id.odoo_dir, filename))
        for path in self.branch_id.addons_path.replace(' ', '').split(','):
            filename = '%s.cloc' % path.split('/')[-1]
            filepaths.append(os.path.join(self.branch_id.os_id.odoo_dir, path, filename))
        missing_files = []
        for filepath in filepaths:
            try:
                filename = os.path.basename(filepath)
                response = self._docker_cli.copy(container, resource=filepath)
                filelike = StringIO.StringIO(response.read())
                tar = tarfile.open(fileobj=filelike)
                content = tar.extractfile(os.path.basename(filepath)).read()
                self.env['ir.attachment'].create({
                    'name': filename,
                    'datas_fname': filename,
                    'datas': base64.b64encode(content),
                    'res_model': self._name,
                    'res_id': self.id,
                })
            except APIError:
                missing_files.append(filename)
            except Exception, e:
                _logger.error(repr(e))
                _logger.error('Error while attaching %s: %s' % (filename, get_exception_message(e)))
        if missing_files:
            _logger.info("The following files are missing: %s" % missing_files)

    def _get_logs(self, filename):
        attachs = self.env['ir.attachment'].search([
            ('datas_fname', '=', filename),
            ('res_model', '=', self._name),
            ('res_id', '=', self.id),
        ], limit=1)
        return attachs and attachs[0].datas and base64.b64decode(attachs[0].datas) or ''

    @staticmethod
    def _is_flake8_error_code(code):
        return code[0] in ('E', 'F') or code == flake8_debugger.DEBUGGER_ERROR_CODE

    @staticmethod
    def _is_flake8_warning_code(code):
        return code[0] in ('W', 'C', 'N') or code in (TODO_ERROR_CODE, flake8_print.PRINT_ERROR_CODE)

    @api.one
    def _load_flake8_logs(self):
        _logger.info('Parsing Flake8 logs for build_%s...' % self.id)
        data = self._get_logs(FLAKE8FILE).split('\n')
        log_obj = self.env['scm.repository.branch.build.log']
        pattern = re.compile(r'([^:]+addons/)(?P<module>[^\/]*)(/)(?P<file>[^:]+):(?P<line>\d*):(\d*): (?P<code>\w*) (?P<exception>[^$]*)')
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
                log_obj.create(vals)

    @api.one
    def _load_test_logs(self):
        _logger.info('Importing test logs for build_%s...' % self.id)
        log_obj = self.env['scm.repository.branch.build.log']
        pattern = re.compile(r'([^:]+addons/)(?P<file>[^$]*)')
        csv_input = cStringIO.StringIO(self._get_logs(TESTFILE))
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
            log_obj.create(vals)

    @api.one
    def _load_coverage_logs(self):
        _logger.info('Parsing coverage logs for build_%s...' % self.id)
        coverage_obj = self.env['scm.repository.branch.build.coverage']
        pattern = re.compile(r'([^:]+addons/)(?P<module>[^\/]*)(/)(?P<file>[^$]*)')
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
            vals['branch_count'] = len([c for c in cls.find('lines').getchildren() if dict(c.items()).get('branch')])
            vals['branch_rate'] = float(cls_info['branch-rate']) * 100
            coverage_obj.create(vals)

    @api.one
    def _set_build_result(self):
        if self.result in ('failed', 'killed') or self._context.get('killed'):
            return
        _logger.info('Getting the result for build_%s...' % self.id)
        lines_count = sum([coverage.line_count for coverage in self.coverage_ids])
        covered_lines_count = sum([coverage.line_rate * coverage.line_count for coverage in self.coverage_ids])
        self.write({
            'quality_code_count': len(self.log_ids.filtered(lambda log: log.type == 'quality_code')),
            'failed_test_count': len(self.log_ids.filtered(lambda log: log.type == 'test' and log.result == 'error')),
            'test_count': len(self.log_ids.filtered(lambda log: log.type == 'test' and log.result != 'ignored')),
            'coverage_avg': lines_count and covered_lines_count / lines_count or 0.0,
            'result': self.log_ids.filtered(lambda log: log.result == 'error') and 'unstable' or 'stable',
        })
        if self.result == 'stable':
            for previous_build in self.branch_id.build_ids:
                if previous_build.id < self.id and previous_build.state in ('running', 'done') \
                        and previous_build.result != 'killed':  # Because builds ordered by id desc
                    if previous_build.result != 'stable':
                        self._send_build_result('Back to stable')
                    break
        elif self.result == 'unstable':
            self._send_build_result('Unstable')

    @api.model
    def _get_action_url(self, **kwargs):
        kwargs['base_url'] = self.env["ir.config_parameter"].get_param('web.base.url')
        return "%(base_url)s/web?#id=%(res_id)s&view_type=%(view_type)s&model=%(model)s&action=%(action_id)s" % kwargs

    @api.one
    def _send_build_result(self, short_message):
        "Send build result and error message to branch followers"
        context = {
            'subject': short_message,
            'build_url': self._get_action_url(**{
                'res_id': self.id, 'model': self._name, 'view_type': 'form',
                'action_id': self.env.ref('smile_ci.action_repository_branch_build').id,
            }),
        }
        if self.commit_logs:
            context['commit_logs'] = tools.plaintext2html(self.commit_logs)
        if self._context.get('build_error'):
            context['build_error'] = tools.plaintext2html(self._context['build_error'])
        template = self.env.ref('smile_ci.email_template_build_result')
        subject = self.env['email.template'].with_context(context).render_template(template.subject, self._name, self.id)
        body = self.env['email.template'].with_context(context).render_template(template.body_html, self._name, self.id)
        self.message_post(body=body, subject=subject, subtype='mail.mt_comment', partner_ids=self.branch_id.partner_ids)

    @api.one
    def _load_logs_in_db(self):
        for log_type in ('test', 'flake8', 'coverage'):
            try:
                getattr(self, '_load_%s_logs' % log_type)()
            except Exception, e:
                _logger.error(repr(e))
                _logger.error('Error while loading %s logs: %s' % (log_type, get_exception_message(e)))

    @api.multi
    def unlink(self):
        self._remove_container()
        return super(Build, self).unlink()

    @api.one
    def _remove_directory(self):
        if self.directory and os.path.exists(self.directory):
            shutil.rmtree(self.directory)

    @api.multi
    def _remove_physical_container(self):
        self.ensure_one()
        _logger.info('Removing container build_%s and its original image...' % self.id)
        try:
            container = self._get_container_name()
            self._docker_cli.remove_container(container, force=True)
            image = self._get_image_name()
            self._docker_cli.remove_image(image, force=True)
        except APIError, e:
            _logger.warning(e)

    @api.one
    def _remove_container(self):
        vals = {'state': 'done'}
        if self.state != 'pending':
            self._remove_physical_container()
        if self.state != 'running':
            vals['result'] = 'killed'
        self.write(vals)

    @api.multi
    def stop_container(self):
        self.ensure_one()
        _logger.info('Build %s was stopped by user %d (%s)...' % (self.id, self._uid, self.env.user.name))
        if self.filtered(lambda build: not build.is_killable):
            raise Warning(_("You can't stop a build if its container has not been started!"))
        self._remove_container()
        return True

    @api.multi
    @api.returns('ir.attachment', lambda value: value.id)
    def export_container(self):
        self.ensure_one()
        _logger.info('Exporting container build_%s...' % self.id)
        container = self._get_container_name()
        archive = self._docker_cli.export(container)
        archive_content = archive.read()
        return self.env['ir.attachment'].create({
            'name': 'Docker Container',
            'datas_fname': 'build_%s.tar' % self.id,
            'datas': base64.b64encode(archive_content),
            'res_model': self._name,
            'res_id': self.id,
        })

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

    @api.multi
    def show_logs(self):
        "Get logs from Docker and show them inside a pop-up."
        self.ensure_one()
        view = self.env.ref('smile_ci.view_build_show_server_logs')
        return self.open_wizard(name='Server logs', view_id=view.id)

    @api.model
    def _get_purge_date(self, age_number, age_type):
        assert isinstance(age_number, (int, long))
        assert age_type in ('years', 'months', 'weeks', 'days', 'hours', 'minutes', 'seconds')
        date = datetime.strptime(fields.Datetime.now(), DATETIME_FORMAT) + relativedelta(**{age_type: -age_number})
        return date.strftime(DATETIME_FORMAT)

    @api.model
    def purge_logs(self, age_number=1, age_type='months'):
        date = self._get_purge_date(age_number, age_type)
        _logger.info('Purging logs created before %s...' % (date,))
        self.env['scm.repository.branch.build.log'].purge(date)
        self.env['scm.repository.branch.build.coverage'].purge(date)
        return True

    @api.model
    def _get_builds_to_purge(self, date):
        return self.search([('create_date', '<=', date)])

    @api.model
    def purge(self, date):
        builds = self._get_builds_to_purge(date)
        return builds.unlink()
