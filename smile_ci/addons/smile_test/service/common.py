# -*- coding: utf-8 -*-

# Because external_dependencies is not supported for Odoo version < 7.0
try:
    import coverage
except ImportError:
    raise ImportError('Please install coverage package')

from distutils.version import LooseVersion
import logging
import os
import subprocess
import sys
import threading

try:
    # For Odoo 10.0
    from odoo import release
    from odoo.service import common
    from odoo.service.db import check_super
    from odoo.tools import config
except ImportError:
    try:
        # For Odoo 9.0
        from openerp import release
        from openerp.service import common
        from openerp.service.db import check_super
        from openerp.tools import config
    except ImportError:
        try:
            # For Odoo 8.0
            from openerp import release
            from openerp.service import common
            from openerp.service.security import check_super
            from openerp.tools import config
        except ImportError:
            try:
                # For Odoo 6.1 and 7.0
                from openerp import release
                from openerp.service.security import check_super
                from openerp.service.web_services import common
                from openerp.tools import config
            except ImportError:
                try:
                    # For Odoo 5.0 and 6.0
                    import release
                    from service.security import check_super
                    from service.web_services import common
                    from tools import config
                except ImportError:
                    raise ImportError("Odoo version not supported")

from .. import tools

_logger = logging.getLogger(__name__)

OMIT_FILES = ['__manifest__.py', '__openerp__.py',
              '__terp__.py', '__init__.py']
OMIT_DIRS = ['web', 'static', 'controllers', 'doc', 'test', 'tests']


class NewServices():

    @staticmethod
    def _get_coverage_sources():
        coverage_sources = []
        if config.get('code_path'):
            for relpath in config['code_path'].split(','):
                for dirpath, dirnames, filenames in os.walk(relpath):
                    for omit in OMIT_DIRS:
                        if '*/%s/*' % omit in dirpath:
                            break
                    else:
                        for filename in filenames:
                            if filename.endswith('.py') and \
                                    filename not in OMIT_FILES:
                                coverage_sources.append(
                                    os.path.join(dirpath, filename))
        return coverage_sources

    @staticmethod
    def coverage_start():
        if hasattr(common, 'coverage'):
            return False
        _logger.info('Starting code coverage...')
        sources = NewServices._get_coverage_sources()
        data_file = config.get('coverage_data_file') or '/tmp/.coverage'
        common.coverage = coverage.coverage(
            branch=True, source=sources, data_file=data_file)
        common.coverage.start()
        return True

    @staticmethod
    def coverage_stop():
        if not hasattr(common, 'coverage'):
            return False
        _logger.info('Stopping code coverage...')
        common.coverage.stop()
        common.coverage.save()
        if config.get('coveragefile'):
            sources = NewServices._get_coverage_sources()
            common.coverage.xml_report(
                morfs=sources, outfile=config['coveragefile'],
                ignore_errors=True)
        del common.coverage
        return True

    @staticmethod
    def check_quality_code():
        _logger.info('Checking code quality...')
        if not config.get('code_path') or not config.get('flake8file'):
            _logger.warning(
                'Incomplete config file: no code_path or no flake8file...')
            return False
        cmd = [sys.executable, '-m', 'flake8']
        max_line_length = config.get('flake8_max_line_length')
        if max_line_length:
            cmd += ['--max-line-length=%s' % max_line_length]
        exclude_files = config.get('flake8_exclude_files')
        if exclude_files:
            cmd += ['--exclude=%s' % exclude_files.replace(' ', '')]
        ignore_codes = config.get('flake8_ignore_codes')
        if ignore_codes:
            cmd += ['--ignore=%s' % ignore_codes.replace(' ', '')]
        cmd += config.get('code_path').split(',')
        with open(config.get('flake8file'), 'a') as f:
            try:
                subprocess.check_output(cmd)
            except subprocess.CalledProcessError as e:
                msg = e.output
                if isinstance(msg, bytes):
                    msg = msg.decode("utf-8")
                f.write(msg)
        return True

    @staticmethod
    def count_lines_of_code():
        _logger.info('Counting lines of code...')
        if not config.get('addons_path'):
            _logger.warning('Incomplete config file: no addons_path...')
            return False
        for path in config.get('addons_path').replace(' ', '').split(','):
            filename = '%s.cloc' % path.split('/')[-1]
            with open(os.path.join(path, filename), 'a') as f:
                cmd = ['cloc', path]
                try:
                    result = subprocess.check_output(cmd)
                    if isinstance(result, bytes):
                        result = result.decode("utf-8")
                    f.write(result)
                except subprocess.CalledProcessError as e:
                    msg = e.output
                    if isinstance(msg, bytes):
                        msg = msg.decode("utf-8")
                    f.write(msg)
        return True

    @staticmethod
    def run_tests(dbname, modules=None, return_logs=False):
        init_test_enable = config.get('test_enable')
        config['test_enable'] = True
        threading.currentThread().dbname = dbname
        modules = tools.filter_modules_list(dbname, modules)
        tools.create_logfile()
        tools.run_unit_tests(dbname, modules)
        tools.run_other_tests(dbname, modules)
        config['test_enable'] = init_test_enable
        if return_logs:
            return tools.read_logs()
        return True

    @staticmethod
    def list_tests(dbname, modules=None):
        modules = tools.filter_modules_list(dbname, modules)
        tests_by_module = tools.get_yaml_test_comments(modules)
        unit_tests_by_module = tools.get_unit_test_docstrings(modules)
        for module, tests in unit_tests_by_module.items():
            tests_by_module.setdefault(module, []).extend(tests)
        return tests_by_module


native_dispatch = common.dispatch
additional_methods = [attr for attr in dir(NewServices)
                      if not attr.startswith('_') and
                      callable(getattr(NewServices, attr))]


def new_dispatch(*args):
    i = LooseVersion(release.major_version) < LooseVersion('8.0') and 1 or 0
    method = args[i]
    if method in additional_methods:
        params = args[i + 1]
        admin_passwd, params = params[0], params[1:]
        check_super(admin_passwd)
        return getattr(NewServices, method)(*params)
    return native_dispatch(*args)


common.dispatch = new_dispatch
