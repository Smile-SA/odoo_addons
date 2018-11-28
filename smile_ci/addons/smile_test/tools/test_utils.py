# -*- coding: utf-8 -*-

import csv
from contextlib import closing
from distutils.version import LooseVersion
import inspect
import logging
import os
from six import string_types
import tempfile
import time
import traceback
import unittest2
import yaml

try:
    # For Python 2
    from xmlrpclib import Fault
except ImportError:
    # For Python 3
    from xmlrpc.client import Fault

try:
    # For Odoo 10.0-higher
    from odoo import release, sql_db, tools
    from odoo.modules.module import get_module_path, \
        load_information_from_description_file
except ImportError:
    try:
        # For Odoo 6.1-9.0
        from openerp import release, sql_db, tools
        from openerp.modules.module import get_module_path, \
            load_information_from_description_file
    except ImportError:
        try:
            # For Odoo 5.0 and 6.0
            from addons import get_module_path, \
                load_information_from_description_file
            import release
            import sql_db
            import tools
        except ImportError:
            raise ImportError("Odoo version not supported")

try:
    # For Odoo >= 8.0
    from odoo.exceptions import except_orm
except ImportError:
    try:
        # For Odoo 6.1 and 7.0
        from openerp.osv.orm import except_orm
    except ImportError:
        try:
            # For Odoo 5.0 and 6.0
            from osv.osv import except_osv as except_orm
        except ImportError:
            raise ImportError("Odoo version not supported")

try:
    # For Odoo 10.0
    from odoo.tests import common as tests_common
    from odoo.modules.module import run_unit_tests
except ImportError:
    try:
        # For Odoo 7.0-9.0
        from openerp.tests import common as tests_common
        from openerp.modules.module import run_unit_tests
    except ImportError:
        run_unit_tests = None

from ..tools import get_test_modules, unwrap_suite

_logger = logging.getLogger(__name__)

KEYS = ['module', 'result', 'code', 'file', 'line', 'exception', 'duration']


def _get_exception_message(e):
    if isinstance(e, except_orm):
        return tools.ustr(e.value)
    if isinstance(e, Fault):
        return tools.ustr(e.faultString)
    if hasattr(e, 'message'):
        return tools.ustr(e.message)
    return tools.ustr(e)


def _get_logfile():
    filename = tools.config.get('test_logfile')
    if not filename:
        tempdir = tempfile.gettempdir()
        filename = os.path.join(tempdir, 'odoo_test_logs.csv')
    return filename


def create_logfile():
    filename = _get_logfile()
    if os.path.exists(filename):
        os.remove(filename)
    with open(filename, 'w') as f:
        writer = csv.writer(f)
        writer.writerow(KEYS)


def _write_log(vals):
    filename = _get_logfile()
    with open(filename, 'a') as f:
        writer = csv.writer(f)
        writer.writerow([tools.ustr(vals.get(key, '')) for key in KEYS])


def read_logs():
    filename = _get_logfile()
    data, errors = [], []
    tests_count = failed_tests_count = duration = 0
    with open(filename) as f:
        for row in csv.DictReader(f):
            data.append('%s (%s)... %s' %
                        (row['file'], row['module'], row['result']))
            if row['result'] != 'ignored':
                tests_count += 1
                duration += float(row['duration'])
            if row['result'] == 'error':
                failed_tests_count += 1
                errors.append('FAIL: %s (%s)' % (row['file'], row['module']))
                errors.append('-' * 80)
                errors.append(row['exception'])
                errors.append('\n' + '-' * 80)
    if failed_tests_count:
        data.append('\n' + '=' * 80)
        data += errors
    data.append("Ran %s tests in %ss" % (tests_count, round(duration, 3)))
    if failed_tests_count:
        data.append("\nFAILED (failures=%s)" % failed_tests_count)
    data.append("\nLogfile: %s" % filename)
    return '\n'.join(data)


def _get_modules_list(dbname):
    db = sql_db.db_connect(dbname)
    with closing(db.cursor()) as cr:
        # INFO: Need to take modules in state 'to upgrade',
        # for compatibility with versions older than 7.0
        # The update of a module was done in two steps :
        # 1) mark module to upgrade, 2) upgrade all marked modules
        cr.execute(
            "SELECT name from ir_module_module WHERE state IN "
            "('installed', 'to upgrade') ORDER BY sequence, name")
        return [name for (name,) in cr.fetchall()]


def filter_modules_list(dbname, modules):
    installed_modules = _get_modules_list(dbname)
    if not modules:
        return installed_modules
    return list(filter(
        lambda module_to_test: module_to_test in installed_modules, modules))


def _get_test_files_by_module(modules):
    assert isinstance(modules, list), 'modules argument should be a list'
    test_files = {}
    for module in modules:
        info = load_information_from_description_file(module)
        test_files[module] = info.get('test', [])
    return test_files


def _run_test(cr, module, filename):
    _, ext = os.path.splitext(filename)
    pathname = os.path.join(module, filename)
    with tools.file_open(pathname) as fp:
        if ext == '.sql':
            if hasattr(tools, 'convert_sql_import'):
                tools.convert_sql_import(cr, fp)
            else:
                queries = fp.read().split(';')
                for query in queries:
                    new_query = ' '.join(query.split())
                    if new_query:
                        cr.execute(new_query)
        elif ext == '.csv':
            tools.convert_csv_import(cr, module, pathname, fp.read(
            ), idref=None, mode='update', noupdate=False)
        elif ext == '.yml':
            if LooseVersion(release.major_version) >= LooseVersion('7.0'):
                tools.convert_yaml_import(
                    cr, module, fp, kind='test', idref=None,
                    mode='update', noupdate=False)
            else:
                tools.convert_yaml_import(
                    cr, module, fp, idref=None, mode='update', noupdate=False)
        elif ext == '.xml':
            tools.convert_xml_import(
                cr, module, fp, idref=None, mode='update', noupdate=False)


def _build_error_message():
    # Yaml traceback doesn't work, certainly because of the compile clause
    # that messes up line numbers
    error_msg = tools.ustr(traceback.format_exc())
    frame_list = inspect.trace()
    deepest_frame = frame_list[-1][0]
    possible_yaml_statement = None
    for frame_inf in frame_list:
        frame = frame_inf[0]
        for local in ('statements', 'code_context', 'model'):
            if local not in frame.f_locals:
                break
        else:
            # all locals found ! we are in process_python function
            possible_yaml_statement = frame.f_locals['statements']
    if possible_yaml_statement:
        numbered_line_statement = ""
        for index, line in enumerate(
                possible_yaml_statement.split('\n'), start=1):
            numbered_line_statement += "%03d>  %s\n" % (index, line)
        yaml_error = "For yaml file, check the line number indicated in " \
                     "the traceback against this statement:\n%s"
        yaml_error = yaml_error % numbered_line_statement
        error_msg += '\n%s' % yaml_error
    error_msg += """\nLocal variables in deepest are: %s """ % repr(
        deepest_frame.f_locals)
    return tools.ustr(error_msg.encode('utf-8'))


def _file_in_requested_directories(test_file):
    test_path = tools.config.get('test_path')
    if not test_path:
        return True
    for code_path in test_path.split(','):
        if os.path.realpath(test_file).startswith(os.path.realpath(code_path)):
            return True
    return False


def run_other_tests(dbname, modules):
    _logger.info('Running tests other than unit...')
    ignore = eval(tools.config.get('ignored_tests') or '{}')
    db = sql_db.db_connect(dbname)
    with closing(db.cursor()) as cr:
        test_files_by_module = _get_test_files_by_module(modules)
        for module in test_files_by_module:
            ignored_files = ignore.get(module, [])
            if ignored_files == 'all':
                ignored_files = test_files_by_module[module]
            for filename in test_files_by_module[module]:
                vals = {
                    'module': module,
                    'file': filename,
                }
                if filename in ignored_files or \
                        not _file_in_requested_directories(
                            get_module_path(module)) or \
                        LooseVersion(
                            release.major_version) >= LooseVersion('12.0'):
                    vals['result'] = 'ignored'
                    _write_log(vals)
                    continue
                start = time.time()
                try:
                    _run_test(cr, module, filename)
                except Exception as e:
                    vals['duration'] = time.time() - start
                    vals['result'] = 'error'
                    vals['code'] = e.__class__.__name__
                    vals['exception'] = '\n%s' % _get_exception_message(e)
                    if filename.endswith('.yml'):
                        vals['exception'] += '\n%s' % _build_error_message()
                    _write_log(vals)
                else:
                    vals['duration'] = time.time() - start
                    vals['result'] = 'success'
                    _write_log(vals)
            cr.rollback()


def run_unit_tests(dbname, modules):
    if run_unit_tests:
        ignore = eval(tools.config.get('ignored_tests') or '{}')
        _logger.info('Running unit tests...')
        tests_common.DB = dbname
        for module in modules:
            for m in get_test_modules(module):
                vals = {'module': module}
                filename = os.path.join('tests', '%s.py' %
                                        m.__name__.split('.')[-1])
                vals['file'] = filename
                if not _file_in_requested_directories(m.__file__) \
                        or filename in ignore.get(module, []) \
                        or ignore.get(module) == 'all':
                    vals['result'] = 'ignored'
                    _write_log(vals)
                    continue
                start = time.time()
                tests = unwrap_suite(
                    unittest2.TestLoader().loadTestsFromModule(m))
                suite = unittest2.TestSuite(tests)
                if suite.countTestCases():
                    result = unittest2.TextTestRunner(verbosity=2).run(suite)
                    if not result.wasSuccessful():
                        vals['duration'] = time.time() - start
                        vals['result'] = 'error'
                        exceptions = map(
                            lambda args: args[1],
                            result.failures + result.errors)
                        vals['exception'] = 'Failed test(s):\n\n%s' % \
                            '\n\n'.join(exceptions)
                        _write_log(vals)
                    else:
                        vals['duration'] = time.time() - start
                        vals['result'] = 'success'
                        _write_log(vals)


def get_unit_test_docstrings(modules):
    ignore = eval(tools.config.get('ignored_tests') or '{}')
    test_docstrings_by_module = {}
    for module in modules:
        module_path = get_module_path(module)
        if not _file_in_requested_directories(module_path) or \
                ignore.get(module) == 'all':
            continue
        res = []
        for module_test in get_test_modules(module):
            module_test_file = module_test.__file__
            if module_test_file.endswith('.pyc'):
                # convert extension from .pyc to .py
                module_test_file = module_test_file[:-1]
            filename = os.path.join('tests', '%s.py' %
                                    module_test_file.split('.')[-1])
            if filename in ignore.get(module, []):
                continue
            root, ext = os.path.splitext(os.path.basename(module_test_file))
            module_classes = [
                module_test.__getattribute__(attr)
                for attr in module_test.__dict__
                if isinstance(module_test.__getattribute__(attr), type)]
            for module_class in module_classes:
                comments = []
                test_methods = [
                    module_class.__dict__[attr]
                    for attr in module_class.__dict__
                    if callable(module_class.__dict__[attr]) and
                    attr.startswith('test')]
                if not test_methods:
                    continue
                if module_class.__dict__['__doc__']:
                    comments.append(module_class.__dict__[
                                    '__doc__'])  # class docstring
                for test_method in sorted(
                        test_methods, key=lambda x: x.__name__):
                    # method name and docstring
                    comment = '%s:\n%s' % (
                        test_method.__name__, test_method.__doc__ or '')
                    comments.append(comment)
                res.append(
                    (root, module_test_file[module_test_file.index(module):],
                     comments))
        if res:
            test_docstrings_by_module[module] = res
    return test_docstrings_by_module


def get_yaml_test_comments(modules):
    if LooseVersion(release.major_version) >= LooseVersion('12.0'):
        # YAML tests are not yet supported since version 12.0
        return {}
    ignore = eval(tools.config.get('ignored_tests') or '{}')
    test_comments_by_module = {}
    tests_by_module = _get_test_files_by_module(modules)
    for module in tests_by_module:
        module_path = get_module_path(module)
        if not _file_in_requested_directories(module_path) or \
                ignore.get(module) == 'all':
            continue
        res = []
        for file_path in tests_by_module[module]:
            if file_path in ignore.get(module, []):
                continue
            fp = os.path.join(module_path, file_path.replace('/', os.path.sep))
            if not os.path.exists(fp):
                _logger.error("No such file: %s", fp)
                continue
            with open(fp) as f_obj:
                root, ext = os.path.splitext(f_obj.name)
                if ext == '.yml':
                    comments = []
                    for node in yaml.load(f_obj.read()):
                        if isinstance(node, string_types):
                            comments.append(node)
                    res.append((os.path.basename(root),
                                os.path.join(module, file_path), comments))
        if res:
            test_comments_by_module[module] = res
    return test_comments_by_module
