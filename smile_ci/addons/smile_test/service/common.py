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

_logger = logging.getLogger(__name__)

OMIT_FILES = ['__manifest__.py', '__openerp__.py', '__terp__.py', '__init__.py']
OMIT_DIRS = ['web', 'static', 'controllers', 'doc', 'test', 'tests']


class NewServices():

    @staticmethod
    def get_coverage_sources():
        coverage_sources = []
        if config.get('code_path'):
            for relpath in config['code_path'].split(','):
                for dirpath, dirnames, filenames in os.walk(relpath):
                    for omit in OMIT_DIRS:
                        if '*/%s/*' % omit in dirpath:
                            break
                    else:
                        for filename in filenames:
                            if filename.endswith('.py') and filename not in OMIT_FILES:
                                coverage_sources.append(os.path.join(dirpath, filename))
        return coverage_sources

    @staticmethod
    def coverage_start():
        if hasattr(common, 'coverage'):
            return False
        _logger.info('Starting code coverage...')
        sources = NewServices.get_coverage_sources()
        data_file = config.get('coverage_data_file') or '/tmp/.coverage'
        common.coverage = coverage.coverage(branch=True, source=sources, data_file=data_file)
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
            sources = NewServices.get_coverage_sources()
            common.coverage.xml_report(morfs=sources, outfile=config['coveragefile'], ignore_errors=True)
        del common.coverage
        return True

    @staticmethod
    def check_quality_code():
        _logger.info('Checking code quality...')
        if not config.get('code_path') or not config.get('flake8file'):
            _logger.warning('Incomplete config file: no code_path or no flake8file...')
            return False
        max_line_length = config.get('flake8_max_line_length') or 79
        exclude_files = config.get('flake8_exclude_files') or '.svn,CVS,.bzr,.hg,.git,__pycache__'
        with open(config.get('flake8file'), 'a') as f:
            for path in config.get('code_path').replace(' ', '').split(','):
                cmd = ['flake8', '--max-line-length=%s' % max_line_length,
                       '--exclude=%s' % exclude_files.replace(' ', ''), path]
                try:
                    subprocess.check_output(cmd)
                except subprocess.CalledProcessError, e:
                    f.write(e.output)
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
                    f.write(subprocess.check_output(cmd))
                except subprocess.CalledProcessError, e:
                    f.write(e.output)
        return True


native_dispatch = common.dispatch


def new_dispatch(*args):
    i = LooseVersion(release.major_version) < LooseVersion('8.0') and 1 or 0
    method = args[i]
    if method in ('coverage_start', 'coverage_stop', 'check_quality_code', 'count_lines_of_code'):
        admin_passwd = args[i + 1][0]
        check_super(admin_passwd)
        return getattr(NewServices, method)()
    return native_dispatch(*args)

common.dispatch = new_dispatch
