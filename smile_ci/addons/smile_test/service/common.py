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

# Because external_dependencies is not supported for Odoo version < 7.0
try:
    import coverage
except ImportError:
    raise ImportError('Please install coverage package')

import os
import subprocess

try:
    # For Odoo 8.0
    from openerp.service import common
    from openerp.tools import config
except ImportError:
    try:
        # For Odoo 6.1 and 7.0
        from openerp.service.web_services import common
        from openerp.tools import config
    except ImportError:
        try:
            # For Odoo 5.0 and 6.0
            from service.web_services import common
            from tools import config
        except ImportError:
            raise ImportError("Odoo version not supported")

OMIT_FILES = ['__odoo__.py', '__openerp__.py', '__terp__.py', '__init__.py']
OMIT_DIRS = ['web', 'static', 'controllers', 'doc', 'test', 'tests']


def get_coverage_sources():
    coverage_sources = []
    if config.get('code_path'):
        for dirpath, dirnames, filenames in os.walk(config['code_path']):
            for omit in OMIT_DIRS:
                if '*/%s/*' % omit in dirpath:
                    break
            else:
                for filename in filenames:
                    if filename.endswith('.py') and filename not in OMIT_FILES:
                        coverage_sources.append(os.path.join(dirpath, filename))
    return coverage_sources


def coverage_start():
    if not hasattr(common, 'coverage'):
        sources = get_coverage_sources()
        common.coverage = coverage.coverage(branch=True, source=sources, data_file='/usr/src/odoo/.coverage')
        common.coverage.start()
        return True
    return False


def coverage_stop():
    if hasattr(common, 'coverage'):
        common.coverage.stop()
        common.coverage.save()
        if config.get('coveragefile'):
            sources = get_coverage_sources()
            common.coverage.xml_report(morfs=sources, outfile=config['coveragefile'], ignore_errors=True)
        del common.coverage
        return True
    return False


def check_quality_code():
    if config.get('code_path') and config.get('flake8file'):
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
    return False


def count_lines_of_code():
    if config.get('addons_path'):
        odoo_dir = '/usr/src/odoo/'
        for path in config.get('addons_path').replace(' ', '').split(','):
            file = '%s.cloc' % path.replace(odoo_dir, '').replace('/', '_')
            with open(odoo_dir + file, 'a') as f:
                cmd = ['cloc', path]
                try:
                    f.write(subprocess.check_output(cmd))
                except subprocess.CalledProcessError, e:
                    f.write(e.output)
        return True
    return False


native_dispatch = common.dispatch


def new_dispatch(*args):
    if args[1] == 'coverage_start':
        return coverage_start()
    elif args[1] == 'coverage_stop':
        return coverage_stop()
    elif args[1] == 'check_quality_code':
        return check_quality_code()
    elif args[1] == 'count_lines_of_code':
        return count_lines_of_code()
    return native_dispatch(*args)

common.dispatch = new_dispatch
