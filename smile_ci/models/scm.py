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
import logging
from lxml import etree
from multiprocessing import Lock, Process
import os
import re
import shutil
import subprocess
import tempfile
import time
import xmlrpclib

from openerp import api, models, fields, SUPERUSER_ID, _
from openerp.tools import config, file_open
from openerp.modules.registry import Registry
import openerp.modules as addons

from openerp.addons.smile_scm.tools import cd

from ..tools import cursor, with_new_cursor, s2human

_logger = logging.getLogger(__package__)

BUILD_RESULTS = [
    ('stable', 'Stable'),
    ('unstable', 'Unstable'),
    ('failed', 'Failed'),
    ('killed', 'Killed'),
]
DBNAME = 'test'
CONFIGFILE = 'server.conf'
COVERAGEFILE = 'coverage.xml'
FLAKE8FILE = 'flake8.log'
LOGFILE = 'server.log'
TESTFILE = 'scm.repository.branch.build.log.csv'


class VersionControlSystem(models.Model):
    _inherit = 'scm.vcs'

    cmd_revno = fields.Char('Get revision number', required=True)


class OdooVersion(models.Model):
    _inherit = 'scm.version'

    server_cmd = fields.Char('Server command', required=True, default='openerp-server')
    required_packages = fields.Text('Required packages', required=True)
    optional_packages = fields.Text('Optional packages')
    web_included = fields.Boolean('Web Included', default=True)


class Branch(models.Model):
    _inherit = 'scm.repository.branch'

    def __init__(self, pool, cr):
        cls = type(self)
        cls._create_build_lock = Lock()
        super(Branch, self).__init__(pool, cr)

    @api.model
    def _get_lang(self):
        lang_infos = self.env['res.lang'].search_read([], ['code', 'name'])
        return [(lang['code'], lang['name']) for lang in lang_infos]

    @api.one
    def _get_last_build_result(self):
        for build in self.build_ids:  # Because builds ordered by id desc
            if build.result:
                self.last_build_result = build.result
                break
        else:
            self.last_build_result = 'unknown'

    @api.model
    def _get_pg_versions(self):
        return [('8.4', '8.4'), ('9.1', '9.1'), ('9.3', '9.3')]

    @api.model
    def _get_py_versions(self):
        return [('2.7', '2.7')]

    @api.one
    def _get_builds_count(self):
        self.builds_count = len(self.build_ids)

    build_ids = fields.One2many('scm.repository.branch.build', 'branch_id', 'Builds', readonly=True)
    use_in_ci = fields.Boolean('Use in Continuous Integration')
    pg_version = fields.Selection('_get_pg_versions', 'PostgreSQL Version', required=True, default='9.3')
    py_version = fields.Selection('_get_py_versions', 'Python Version', required=True, default='2.7')
    dump_file = fields.Binary('Dump file')
    modules_to_install = fields.Char('Modules to install')
    ignored_tests = fields.Char('Tests to ignore', help='module.filename, without extension. Comma-separated')
    server_path = fields.Char('Server path', default="server")
    addons_path = fields.Char('Addons path', default="addons", help="Comma-separated")
    code_path = fields.Char('Source code to analyse path', help="Addons path for which checking code quality and coverage.\n"
                                                                "If empty, all source code is checked.")
    workers = fields.Integer('Workers', default=0, required=True)
    user_uid = fields.Integer('Admin id', default=1, required=True)
    user_passwd = fields.Char('Admin password', default='admin', required=True)
    lang = fields.Selection('_get_lang', 'Language', default='en_US', required=True)
    last_build_result = fields.Selection(BUILD_RESULTS + [('unknown', 'Unknown')], 'Last result',
                                         compute='_get_last_build_result', store=False)
    builds_count = fields.Integer('Builds Count', compute='_get_builds_count', store=False)

    @api.one
    def _update(self):
        if self.state == 'draft':
            return self.clone()
        return self.pull()

    @api.multi
    def _get_revno(self):
        assert len(self) == 1, 'ids must be a list with only one item!'
        branch = self[0]
        revno = ''
        with cd(branch.directory):
            vcs = branch.vcs_id
            cmd_revno = vcs.cmd_revno % {'branch': branch.branch}
            cmd = cmd_revno.split(' ')
            cmd.insert(0, vcs.cmd)
            revno = subprocess.check_output(cmd)
        return revno

    @api.multi
    def _changes(self):
        assert len(self) == 1, 'ids must be a list with only one item!'
        branch = self[0]
        if not branch.build_ids or branch._get_revno() != branch.build_ids[0].revno.encode('utf8'):  # Because builds ordered by id desc
            return True
        return False

    @api.one
    def create_build(self, force=False):
        with self._create_build_lock:
            self._create_build(force)
        return True

    @api.one
    def _create_build(self, force=False):
        if self.use_in_ci:
            self._update()
            if self._changes() or force:
                vals = {'branch_id': self.id, 'revno': self._get_revno()}
                self.env['scm.repository.branch.build'].create(vals)

    @api.one
    def force_create_build(self):
        return self.create_build(force=True)

    @api.model
    def create_builds(self):
        """Method called by a scheduled action executed each X-minutes"""
        branches = self.search([('use_in_ci', '=', True)])
        branches.create_build()
        return True


def state_cleaner(method):
    def new_load(self, cr, module):
        res = method(self, cr, module)
        build_obj = self.get('scm.repository.branch.build')
        if build_obj:
            cr.execute("select relname from pg_class where relname='%s'" % build_obj._table)
            if cr.rowcount:
                # Search testing builds
                build_ids = build_obj.search(cr, SUPERUSER_ID, [('state', '=', 'testing')])
                branch_ids = [b['branch_id'] for b in build_obj.read(cr, SUPERUSER_ID, build_ids, ['branch_id'], load='_classic_write')]
                # Search running builds not running anymore
                runnning_build_ids = build_obj.search(cr, SUPERUSER_ID, [('state', '=', 'running')])
                actual_runnning_build_ids = [int(row.split('build_')[1].replace(' ', ''))
                                             for row in subprocess.check_output(["docker", "ps"]).split('\n')[1:]
                                             if 'build_' in row]
                build_ids += list(set(runnning_build_ids) - set(actual_runnning_build_ids))
                if build_ids:
                    # Kill invalid builds
                    build_obj._remove_container(cr, SUPERUSER_ID, build_ids)
                    build_obj.write(cr, SUPERUSER_ID, build_ids, {'state': 'done', 'result': 'killed'})
                # Force build creation for branch in test before server stop
                self.get('scm.repository.branch').force_create_build(cr, SUPERUSER_ID, branch_ids)
        return res
    return new_load


class Build(models.Model):
    _name = 'scm.repository.branch.build'
    _description = 'Build'
    _inherit = ['mail.thread']
    _rec_name = 'id'
    _order = 'id desc'
    _track = {}  # Create message and trigger in status

    def __init__(self, pool, cr):
        cls = type(self)
        cls._scheduler_lock = Lock()
        super(Build, self).__init__(pool, cr)
        setattr(Registry, 'load', state_cleaner(getattr(Registry, 'load')))

    @api.one
    @api.depends('date_start', 'date_stop')
    def _get_time(self):
        if not (self.date_start and self.date_stop):
            self.time = 0
        else:
            timedelta = fields.Datetime.from_string(self.date_stop) \
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
        last_builds = [b for b in self.branch_id.build_ids
                       if b.result in ('unstable', 'stable')
                       and b.id < self.id]
        if last_builds:
            self.last_build_time_human = last_builds[0].time_human
        else:
            self.last_build_time_human = ''

    @api.one
    def _quality_code_count(self):
        self.quality_code_count = len(filter(lambda log: log.type == 'quality_code', self.log_ids))

    @api.one
    def _failed_test_count(self):
        self.failed_test_count = len(filter(lambda log: log.type == 'test' and log.result == 'error', self.log_ids))

    @api.one
    def _coverage_avg(self):
        line_counts = sum([coverage.line_count for coverage in self.coverage_ids])
        self.coverage_avg = line_counts and \
            sum([coverage.line_rate * coverage.line_count for coverage in self.coverage_ids]) / line_counts or 0

    id = fields.Integer('Number', readonly=True)
    branch_id = fields.Many2one('scm.repository.branch', 'Branch', required=True, readonly=True)
    revno = fields.Char('Last revision number', required=True, readonly=True)
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
    host = fields.Char(readonly=True, default='localhost')
    port = fields.Char(readonly=True)
    date_start = fields.Datetime('Start date', readonly=True)
    date_stop = fields.Datetime('End date', readonly=True)
    time = fields.Integer(compute='_get_time')
    age = fields.Integer(compute='_get_age')
    time_human = fields.Char('Time', compute='_convert_time_to_human', store=False)
    age_human = fields.Char('Age', compute='_convert_age_to_human', store=False)
    last_build_time_human = fields.Char('Last build time', compute='_get_last_build_time_human', store=False)
    log_ids = fields.One2many('scm.repository.branch.build.log', 'build_id', 'Logs', readonly=True)
    coverage_ids = fields.One2many('scm.repository.branch.build.coverage', 'build_id', 'Coverage', readonly=True)
    quality_code_count = fields.Integer('# Quality code', compute='_quality_code_count', store=False)
    failed_test_count = fields.Integer('# Faliled tests', compute='_failed_test_count', store=False)
    coverage_avg = fields.Integer('Coverage average', compute='_coverage_avg', store=False)

    @property
    def _builds_path(self):
        builds_path = config.get('builds_path') or tempfile.gettempdir()
        if not os.path.isdir(builds_path):
            raise Warning(_("%s doesn't exist or is not a directory") % builds_path)
        return builds_path

    @api.model
    def create(self, vals):
        build = super(Build, self).create(vals)
        build._copy_sources()
        return build

    @api.one
    def _copy_sources(self):
        _logger.info('Copying %s %s sources...' % (self.branch_id.name, self.branch_id.branch))
        self.directory = os.path.join(self._builds_path, str(self.id))
        ignore_patterns = shutil.ignore_patterns('.svn', '.git', '.bzr', '.hg', '*.pyc', '*.pyo', '*~', '~*')
        shutil.copytree(self.branch_id.directory, self.directory, ignore=ignore_patterns)
        self._add_ci_addons()

    @api.one
    def _add_ci_addons(self):
        for adp in addons.module.ad_paths:
            ci_addons_path = os.path.join(adp, 'smile_ci/addons')
            if os.path.exists(ci_addons_path):
                break
        else:
            raise IOError("smile_ci/addons is not found")
        ignore_patterns = shutil.ignore_patterns('.svn', '.git', '.bzr', '.hg', '*.pyc', '*.pyo', '*~', '~*')
        with cd(self.directory):
            shutil.copytree(ci_addons_path, 'ci-addons', ignore=ignore_patterns)

    def write_with_new_cursor(self, vals):
        with cursor(self._cr) as new_cr:
            return self.with_env(self.env(cr=new_cr)).write(vals)

    @api.model
    def scheduler(self):
        with self._scheduler_lock:
            self._scheduler()
        return True

    @api.model
    def _scheduler(self):
        testing = self.search_count([('state', '=', 'testing')])
        max_testing = self.env['ir.config_parameter'].get_param('ci.max_testing')
        builds_to_run = self.search([('branch_id.use_in_ci', '=', True),
                                     ('state', '=', 'pending')], order='id asc')
        ports = sorted(self._find_ports(), reverse=True)
        for build in builds_to_run:
            testing += 1
            if testing > max_testing:
                break
            # Use a new cursor to avoid concurrent update if loop is longer than build test
            build.write_with_new_cursor({
                'state': 'testing',
                'result': '',
                'date_start': fields.Datetime.now(),
                'port': ports.pop(),
            })
            # Use a new thread in order to launch other build tests without waiting the end of the first one
            build._test_in_new_thread()
            time.sleep(0.1)  # ?!!

    @api.one
    def _test_in_new_thread(self):
        new_thread = Process(target=self._test)
        new_thread.start()

    @api.one
    @with_new_cursor
    def _test(self):
        _logger.info('Testing build %s...' % self.id)
        running = False
        try:
            self._check_quality_code()
            self._count_lines_of_code()
            self._create_configfile()
            self._create_launcherfile()
            self._create_dockerfile()
            self._build_container()
            self._run_container()
            if self.branch_id.dump_file:
                self._restore_db()
            else:
                self._create_db()
            self._install_modules(['smile_test'])
            self._start_coverage()
            if self.branch_id.modules_to_install:
                modules_to_install = self.branch_id.modules_to_install.replace(' ', '').split(',')
                self._install_modules(modules_to_install)
            self._stop_coverage()
        except Exception, e:
            _logger.error(repr(e))
            self.write({'state': 'done', 'result': 'failed', 'date_stop': fields.Datetime.now()})
            self.branch_id.message_post(body=_('Failed'))
            self._remove_container(remove_directory=False)
        else:
            self.write({'state': 'running', 'date_stop': fields.Datetime.now()})
            if self.branch_id.version_id.web_included:
                # Use a new cursor to see running builds, even those started after the begin of this test
                self._check_running()
                running = True
            else:
                self._remove_container(remove_directory=False)
        finally:
            self._attach_files()
            if not running:
                self._remove_directory()
            self._load_logs_in_db()

    @api.model
    @with_new_cursor
    def _check_running(self):
        running = self.search([('state', '=', 'running')], order='date_start desc')
        max_running = int(self.env['ir.config_parameter'].get_param('ci.max_running'))
        if len(running) > max_running:
            running[max_running:]._remove_container()

    @api.one
    def _check_quality_code(self):
        _logger.info('Checking quality code for build:%s...' % self.id)
        if not self.branch_id.code_path:
            return
        param_obj = self.env['ir.config_parameter']
        max_line_length = param_obj.get_param('ci.flake8.max_line_length') or 79
        exclude_files = param_obj.get_param('ci.flake8.exclude_files') or ''
        with cd(self.directory):
            with open(FLAKE8FILE, 'a') as f:
                for path in self.branch_id.code_path.replace(' ', '').split(','):
                    cmd = ['flake8', '--max-line-length=%s' % max_line_length,
                           '--exclude=%s' % exclude_files.replace(' ', ''), path]
                    try:
                        subprocess.check_output(cmd)
                    except subprocess.CalledProcessError, e:
                        f.write(e.output)

    @api.one
    def _count_lines_of_code(self):
        _logger.info('Counting lines of code for build:%s...' % self.id)

        with cd(self.directory):
            for path in self.branch_id.addons_path.split(','):
                file = '%s.cloc' % path
                with open(file, 'a') as f:
                    cmd = ['cloc', path]
                    try:
                        f.write(subprocess.check_output(cmd))
                    except subprocess.CalledProcessError, e:
                        f.write(e.output)

    def _get_options(self):
        branch = self.branch_id

        def format(path):
            if not path:
                return path
            path = path[:]  # To avoid to update database when call replace method - A behaviour caused by new api
            return ','.join(map(lambda p: os.path.join('/usr/src/odoo', p),
                                path.replace(' ', '').split(',')))

        return {
            'db_user': 'odoo',
            'db_password': 'odoo',
            'logfile': format(LOGFILE),
            'coveragefile': format(COVERAGEFILE),
            'code_path': format(self.branch_id.code_path),
            'addons_path': format(branch.addons_path + ',ci-addons'),
            'ignored_tests': format(branch.ignored_tests),
            'test_logfile': format(TESTFILE),
            'test_enable': True,
            'test_disable': False,
            'log_level': 'test',
            'log_handler': "[':TEST']",
            'admin_passwd': self.env['ir.config_parameter'].get_param('ci.admin_passwd'),
            'lang': branch.lang,
            'db_template': 'template0',
            'workers': branch.workers,
        }

    @api.one
    def _create_configfile(self):
        _logger.info('Generating configfile for build:%s...' % self.id)
        options = self._get_options()
        with cd(self.directory):
            with open(CONFIGFILE, 'w') as cfile:
                cfile.write('[options]\n')
                for k, v in options.iteritems():
                    cfile.write('%s = %s\n' % (k, v))

    @api.one
    def _create_launcherfile(self):
        _logger.info('Generating launcherfile for build:%s...' % self.id)
        with file_open('smile_ci/data/launcher.tmpl') as f:
            content = f.read()
        server_cmd = os.path.join(self.branch_id.server_path,
                                  self.branch_id.version_id.server_cmd)
        if server_cmd.startswith('./'):
            server_cmd = server_cmd[2:]
        with cd(self.directory):
            with open('launcher.sh', 'w') as f:
                f.write(content % {'server_cmd': server_cmd})
            os.chmod('launcher.sh', 0775)

    @api.one
    def _create_dockerfile(self):
        _logger.info('Generating dockerfile for build:%s...' % self.id)
        with file_open('smile_ci/data/Dockerfile.tmpl') as f:
            content = f.read()
        localdict = {
            'pg_version': self.branch_id.pg_version,
            'py_version': self.branch_id.py_version,
            'required_packages': self.branch_id.version_id.required_packages or '',
            'optional_packages': self.branch_id.version_id.optional_packages or '',
            'configfile': CONFIGFILE,
        }
        with cd(self.directory):
            with open('Dockerfile', 'w') as f:
                f.write(content % localdict)

    @api.one
    def _build_container(self):
        _logger.info('Building container build:%s...' % self.id)
        cmd = ['docker']
        dns = self.env['ir.config_parameter'].get_param('ci.dns').replace(' ', '')
        for dn in dns.split(','):
            cmd.extend(['--dns', dn])
        cmd.extend(['build', '-t', 'build:%s' % self.id, self.directory])
        subprocess.check_call(cmd)

    @api.one
    def _run_container(self):
        _logger.info('Running container build:%s and expose it in port %s...' % (self.id, self.port))
        cmd = ['docker']
        dns = self.env['ir.config_parameter'].get_param('ci.dns').replace(' ', '')
        for dn in dns.split(','):
            cmd.extend(['--dns', dn])
        cmd.extend(['run', '--name', 'build_%s' % self.id, '-d',
                    '-v', '%s:/usr/src/odoo:rw' % self.directory,
                    '-p', '%s:8069' % self.port, 'build:%s' % self.id])
        subprocess.check_call(cmd)
        # Check Odoo is running (during 1 minute max.)
        t0 = time.time()
        sock_db = self._connect('db')
        while True:
            try:
                sock_db.server_version()
                break
            except Exception, e:
                if time.time() - t0 >= 60:
                    raise e

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
        assert len(self) == 1, 'ids must be a list with only one item!'
        build = self[0]
        url = 'http://%s:%s/xmlrpc/%s' % (build.host, build.port, service)
        return xmlrpclib.ServerProxy(url)

    @api.one
    def _create_db(self):
        _logger.info('Creating database for build:%s...' % self.id)
        branch = self.branch_id
        admin_passwd = self.env['ir.config_parameter'].get_param('ci.admin_passwd')
        sock_db = self._connect('db')
        if sock_db.server_version()[:3] >= '6.1':
            sock_db.create_database(admin_passwd, DBNAME, True, branch.lang, branch.user_passwd)
        else:
            db_id = sock_db.create(admin_passwd, DBNAME, True, branch.lang, branch.user_passwd)
            while True:
                progress = self.sock_db.get_progress(admin_passwd, db_id)[0]
                if progress == 1.0:
                    break
                else:
                    time.sleep(1)

    @api.one
    def _restore_db(self):
        _logger.info('Restoring database for build:%s from file %s...' % (self.id, self.branch_id.dump_file))
        admin_passwd = self.env['ir.config_parameter'].get_param('ci.admin_passwd')
        sock_db = self._connect('db')
        sock_db.restore(admin_passwd, DBNAME, self.branch_id.dump_file)

    @api.one
    def _install_modules(self, modules_to_install):
        _logger.info('Installing modules %s for build:%s...' % (modules_to_install, self.id))
        branch = self.branch_id
        sock_object = self._connect('object')
        sock_exec = lambda *args: sock_object.execute(DBNAME, branch.user_uid, branch.user_passwd, *args)
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
            raise Exception(f.faultString)

    @api.one
    def _start_coverage(self):
        _logger.info('Starting code coverage for build:%s...' % self.id)
        self._connect('common').coverage_start()

    @api.one
    def _stop_coverage(self):
        _logger.info('Stopping code coverage for build:%s...' % self.id)
        self._connect('common').coverage_stop()

    @api.one
    def _attach_files(self):
        _logger.info('Attaching files for build:%s...' % self.id)
        attach_obj = self.env['ir.attachment']
        if not os.path.exists(self.directory):
            return True
        with cd(self.directory):
            cloc_paths = ['%s.cloc' % path for path in self.branch_id.addons_path.split(',')]
            for filename in [CONFIGFILE, COVERAGEFILE, LOGFILE, FLAKE8FILE, TESTFILE] + cloc_paths:
                if not os.path.exists(filename):
                    continue
                with open(filename) as f:
                    attach_obj.create({
                        'name': filename,
                        'datas_fname': filename,
                        'datas': base64.b64encode(f.read()),
                        'res_model': self._name,
                        'res_id': self.id,
                    })

    def _get_logs(self, filename):
        attachs = self.env['ir.attachment'].search([
            ('datas_fname', '=', filename),
            ('res_model', '=', self._name),
            ('res_id', '=', self.id),
        ], limit=1)
        return attachs and attachs[0].datas and base64.b64decode(attachs[0].datas) or ''

    @api.one
    def _load_flake8_logs(self):
        _logger.info('Parsing Flake8 logs for build:%s...' % self.id)
        data = self._get_logs(FLAKE8FILE).split('\n')
        log_obj = self.env['scm.repository.branch.build.log']
        pattern = re.compile(r'(?P<file>[^:]+):(?P<line>\d*):(\d*): (?P<code>\w*) (?P<name>[^$]*)')
        for line in data:
            m = pattern.match(line)
            if m:
                vals = m.groupdict()
                vals['build_id'] = self.id
                vals['type'] = 'quality_code'
                code = vals['code']
                if code[0] in ('E', 'F'):
                    vals['result'] = 'error'
                elif code[0] in ('W', 'C', 'N'):
                    vals['result'] = 'warning'
                log_obj.create(vals)

    @api.one
    def _load_test_logs(self):
        _logger.info('Importing test logs for build:%s...' % self.id)
        log_obj = self.env['scm.repository.branch.build.log']
        pattern = re.compile(r'([^:]+addons/)(?P<file>[^$]*)')
        csv_input = cStringIO.StringIO(self._get_logs(TESTFILE))
        reader = csv.DictReader(csv_input)
        for vals in reader:
            file = vals['file']
            if file:
                match = pattern.match(file)
                if match:
                    vals['file'] = match.groupdict()['file']
            vals['build_id'] = self.id
            vals['code'] = 'TEST'
            vals['type'] = 'test'
            log_obj.create(vals)

    @api.one
    def _load_coverage_logs(self):
        _logger.info('Parsing coverage logs for build:%s...' % self.id)
        coverage_obj = self.env['scm.repository.branch.build.coverage']
        pattern = re.compile(r'([^:]+addons/)(?P<module>[^\/]*)(/)(?P<file>[^$]*)')
        root = etree.fromstring(self._get_logs(COVERAGEFILE))
        for cls in root.xpath('//class'):
            vals = {}
            cls_info = dict(cls.items())
            match = pattern.match(cls_info['name'])
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
        _logger.info('Getting the result for build:%s...' % self.id)
        if not self.result:
            self.result = [log for log in self.log_ids if log.result == 'error'] and 'unstable' or 'stable'
            if self.result == 'stable':
                for previous_build in self.branch_id.build_ids:
                    if previous_build.id < self.id and previous_build.state in ('running', 'done') \
                            and previous_build.result != 'killed':  # Because builds ordered by id desc
                        if previous_build.result != 'stable':
                            self.branch_id.message_post(body=_('Back to stable'))
                        break
            elif self.result == 'unstable':
                self.branch_id.message_post(body=_('Unstable'))

    @api.multi
    def _load_logs_in_db(self):
        try:
            self._load_test_logs()
            self._load_flake8_logs()
            self._load_coverage_logs()
        except:
            _logger.warn('Something was wrong during the loading of logs for build:%s...' % self.id)
            self.result = 'failed'
        else:
            self._set_build_result()

    @api.multi
    def unlink(self):
        self._remove_container()
        return super(Build, self).unlink()

    @api.one
    def _remove_directory(self):
        if os.path.exists(self.directory):
            shutil.rmtree(self.directory)

    @api.one
    def _remove_container(self, remove_directory=True):
        container = 'build_%s' % self.id
        image = 'build:%s' % self.id
        _logger.info('Killing container %s...' % image)
        try:
            running_containers = subprocess.check_output(['docker', 'ps'])
            if container in running_containers:
                subprocess.check_call(['docker', 'stop', container])
            subprocess.check_call(['docker', 'rm', container])
            subprocess.check_call(['docker', 'rmi', '-f', image])
        except subprocess.CalledProcessError:
            pass
        finally:
            if remove_directory:
                self._remove_directory()
            vals = {'state': 'done'}
            if not self.result:
                vals['result'] = 'killed'
            self.write(vals)

    @api.one
    def stop_container(self):
        self._remove_container()
        return True

    @api.multi
    def open(self):
        assert len(self) == 1, 'ids must be a list with only one item!'
        build = self[0]
        return {
            'name': _('Open URL'),
            'type': 'ir.actions.act_url',
            'url': 'http://%s:%s/' % (build.host, build.port),
            'target': 'new',
        }


class Log(models.Model):
    _name = 'scm.repository.branch.build.log'
    _description = 'Log'
    _rec_name = 'file'

    build_id = fields.Many2one('scm.repository.branch.build', 'Build', readonly=True, required=True, ondelete='cascade')
    branch_id = fields.Many2one('scm.repository.branch', 'Branch', readonly=True, related='build_id.branch_id', store=True)
    type = fields.Selection([
        ('quality_code', 'Quality code'),
        ('test', 'Test')
    ], required=True)
    result = fields.Selection([
        ('error', 'Error'),
        ('warning', 'Warning'),
        ('success', 'Success'),
        ('ignored', 'Ignored')
    ], required=True)
    module = fields.Char(readonly=True)
    file = fields.Char(readonly=True)
    line = fields.Integer(readonly=True, group_operator="count")
    code = fields.Char('Class', readonly=True, required=True)
    name = fields.Char('Description', readonly=True)


class Coverage(models.Model):
    _name = 'scm.repository.branch.build.coverage'
    _description = 'Code Coverage'
    _rec_name = 'file'

    build_id = fields.Many2one('scm.repository.branch.build', 'Build', readonly=True, required=True, ondelete='cascade')
    branch_id = fields.Many2one('scm.repository.branch', 'Branch', readonly=True, related='build_id.branch_id', store=True)
    module = fields.Char(readonly=True)
    file = fields.Char(readonly=True)
    line_count = fields.Integer('# lines', readonly=True)
    line_rate = fields.Float('Lines rate', digits=(5, 2), readonly=True)
    branch_count = fields.Integer('# conditionals', readonly=True)
    branch_rate = fields.Float('Conditionals rate', digits=(5, 2), readonly=True)

    def read_group(self, cr, uid, domain, fields, groupby, offset=0, limit=None, context=None, orderby=False, lazy=True):
        fields_to_compute = []
        for field in ('line_rate', 'branch_rate'):
            if field in fields:
                fields.remove(field)
                fields_to_compute.append(field)
        res = super(Coverage, self).read_group(cr, uid, domain, fields, groupby, offset, limit, context, orderby, lazy)
        if fields_to_compute:
            fields_to_search = ['line_count', 'branch_count', 'branch_rate', 'line_rate']
            for group in res:
                if group.get('__domain'):
                    line_infos = self.search_read(cr, uid, group['__domain'], fields_to_search, context=context)
                    line_counts = sum([l['line_count'] for l in line_infos])
                    branch_counts = sum([l['branch_count'] for l in line_infos])
                    group['line_rate'] = line_counts and \
                        sum([l['line_rate'] * l['line_count'] for l in line_infos]) / line_counts or 0
                    group['branch_rate'] = branch_counts and \
                        sum([l['branch_rate'] * l['branch_count'] for l in line_infos]) / branch_counts or 0
        return res
