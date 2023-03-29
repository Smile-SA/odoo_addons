# -*- coding: utf-8 -*-

from contextlib import closing
import csv
import logging
import os
import shutil
import tempfile
import unittest
import xmlrunner
from xmlrpc.client import Fault

from odoo import sql_db, tools
from odoo.exceptions import except_orm
from odoo.modules.module import get_module_path
from odoo.tests import common as tests_common

from ..tools import get_test_modules, unwrap_suite

_logger = logging.getLogger(__name__)


KEYS = ["module", "result", "code", "file", "line", "exception", "duration"]


def _get_exception_message(e):
    if isinstance(e, except_orm):
        return tools.ustr(e.value)
    if isinstance(e, Fault):
        return tools.ustr(e.faultString)
    return tools.ustr(e.message) if hasattr(e, "message") else tools.ustr(e)


def _get_coverage_result_file():
    coverage_result_file = tools.config.get("coverage_result_file")
    if not coverage_result_file:
        tempdir = tempfile.gettempdir()
        coverage_result_file = os.path.join(tempdir, "coverage_result.xml")
    return coverage_result_file


def _get_test_result_directory():
    test_result_directory = tools.config.get("test_result_directory")
    if not test_result_directory:
        tempdir = tempfile.gettempdir()
        test_result_directory = os.path.join(tempdir, "tests")
    return test_result_directory


def _get_logfile():
    filename = tools.config.get("test_logfile")
    if not filename:
        tempdir = tempfile.gettempdir()
        filename = os.path.join(tempdir, "odoo_test_logs.csv")
    return filename


def create_logfile():
    filename = _get_logfile()
    if os.path.exists(filename):
        os.remove(filename)
    with open(filename, "w") as f:
        writer = csv.writer(f)
        writer.writerow(KEYS)


def _write_log(vals):
    filename = _get_logfile()
    with open(filename, "a") as f:
        writer = csv.writer(f)
        writer.writerow([tools.ustr(vals.get(key, "")) for key in KEYS])


def read_logs():
    filename = _get_logfile()
    data, errors = [], []
    tests_count = failed_tests_count = duration = 0
    with open(filename) as f:
        for row in csv.DictReader(f):
            data.append(f'{row["file"]} ({row["module"]})... {row["result"]}')
            if row["result"] != "ignored":
                tests_count += 1
                duration += float(row["duration"])
            if row["result"] == "error":
                failed_tests_count += 1
                errors.extend(
                    (
                        f'FAIL: {row["file"]} ({row["module"]})',
                        "-" * 80,
                        row["exception"],
                        "\n" + "-" * 80,
                    )
                )
    if failed_tests_count:
        data.append("\n" + "=" * 80)
        data += errors
    data.append(f"Ran {tests_count} tests in {round(duration, 3)}s")
    if failed_tests_count:
        data.append("\nFAILED (failures=%s)" % failed_tests_count)
    data.append("\nLogfile: %s" % filename)
    return "\n".join(data)


def _get_modules_list(dbname):
    db = sql_db.db_connect(dbname)
    with closing(db.cursor()) as cr:
        # INFO: Need to take modules in state 'to upgrade',
        # for compatibility with versions older than 7.0
        # The update of a module was done in two steps :
        # 1) mark module to upgrade, 2) upgrade all marked modules
        cr.execute(
            "SELECT name from ir_module_module WHERE state IN "
            "('installed', 'to upgrade') ORDER BY sequence, name"
        )
        return [name for (name,) in cr.fetchall()]


def filter_modules_list(dbname, modules):
    installed_modules = _get_modules_list(dbname)
    return (
        list(
            filter(
                lambda module_to_test: module_to_test in installed_modules,
                modules,
            )
        )
        if modules
        else installed_modules
    )


def _run_test(cr, module, filename):
    _, ext = os.path.splitext(filename)
    pathname = os.path.join(module, filename)
    with tools.file_open(pathname) as fp:
        if ext == ".sql":
            if hasattr(tools, "convert_sql_import"):
                tools.convert_sql_import(cr, fp)
            else:
                queries = fp.read().split(";")
                for query in queries:
                    if new_query := " ".join(query.split()):
                        cr.execute(new_query)
        elif ext == ".csv":
            tools.convert_csv_import(
                cr,
                module,
                pathname,
                fp.read(),
                idref=None,
                mode="update",
                noupdate=False,
            )
        elif ext == ".xml":
            tools.convert_xml_import(
                cr, module, fp, idref=None, mode="update", noupdate=False
            )


def _file_in_requested_directories(test_file):
    test_path = tools.config.get("test_path")
    return (
        any(
            os.path.realpath(test_file).startswith(os.path.realpath(code_path))
            for code_path in test_path.split(",")
        )
        if test_path
        else True
    )


def run_unit_tests(dbname, modules):
    if not run_unit_tests:
        return
    ignore = eval(tools.config.get("ignored_tests") or "{}")
    _logger.info("Running unit tests...")
    tests_common.DB = dbname
    test_result_directory = _get_test_result_directory()
    for module in modules:
        for m in get_test_modules(module):
            filename = os.path.join("tests", f'{m.__name__.split(".")[-1]}.py')
            vals = {"module": module, "file": filename}
            if (
                not _file_in_requested_directories(m.__file__)
                or filename in ignore.get(module, [])
                or ignore.get(module) == "all"
            ):
                vals["result"] = "ignored"
                _write_log(vals)
                continue
            tests = unwrap_suite(unittest.TestLoader().loadTestsFromModule(m))
            suite = unittest.TestSuite(tests)
            if suite.countTestCases():
                xmlrunner.XMLTestRunner(
                    output=test_result_directory, verbosity=2
                ).run(suite)


def get_unit_test_docstrings(modules):
    ignore = eval(tools.config.get("ignored_tests") or "{}")
    test_docstrings_by_module = {}
    for module in modules:
        module_path = get_module_path(module)
        if (
            not _file_in_requested_directories(module_path)
            or ignore.get(module) == "all"
        ):
            continue
        res = []
        for module_test in get_test_modules(module):
            module_test_file = module_test.__file__
            if module_test_file.endswith(".pyc"):
                # convert extension from .pyc to .py
                module_test_file = module_test_file[:-1]
            filename = os.path.join(
                "tests", f'{module_test_file.split(".")[-1]}.py'
            )
            if filename in ignore.get(module, []):
                continue
            root, ext = os.path.splitext(os.path.basename(module_test_file))
            module_classes = [
                module_test.__getattribute__(attr)
                for attr in module_test.__dict__
                if isinstance(module_test.__getattribute__(attr), type)
            ]
            for module_class in module_classes:
                test_methods = [
                    module_class.__dict__[attr]
                    for attr in module_class.__dict__
                    if callable(module_class.__dict__[attr])
                    and attr.startswith("test")
                ]
                if not test_methods:
                    continue
                comments = []
                if module_class.__dict__["__doc__"]:
                    comments.append(
                        module_class.__dict__["__doc__"]
                    )  # class docstring
                comments.extend(
                    "%s:\n%s"
                    % (
                        test_method.__name__,
                        test_method.__doc__ or "",
                    )
                    for test_method in sorted(
                        test_methods, key=lambda x: x.__name__
                    )
                )
                res.append(
                    (
                        root,
                        module_test_file[module_test_file.index(module):],
                        comments,
                    )
                )
        if res:
            test_docstrings_by_module[module] = res
    return test_docstrings_by_module


def _remove_results_files():
    filepath = _get_coverage_result_file()
    dirpath = _get_test_result_directory()
    if os.path.exists(filepath):
        os.remove(filepath)
    if os.path.exists(dirpath) and os.path.isdir(dirpath):
        shutil.rmtree(dirpath)
