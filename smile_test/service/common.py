# -*- coding: utf-8 -*-

import coverage
import logging
import os
import threading

from odoo.service import common
from odoo.service.db import check_super
from odoo.tests.common import BaseCase
from odoo.tools import config

from .. import tools

_logger = logging.getLogger(__name__)

OMIT_FILES = [
    "__manifest__.py",
    "__init__.py",
]
OMIT_DIRS = ["web", "static", "controllers", "doc", "tests"]


class NewServices:
    @staticmethod
    def _get_coverage_sources():
        coverage_sources = []
        if config.get("code_path"):
            for relpath in config["code_path"].split(","):
                for dirpath, dirnames, filenames in os.walk(relpath):
                    for omit in OMIT_DIRS:
                        if f"*/{omit}/*" in dirpath:
                            break
                    else:
                        coverage_sources.extend(
                            os.path.join(dirpath, filename)
                            for filename in filenames
                            if (
                                filename.endswith(".py")
                                and filename not in OMIT_FILES
                            )
                        )
        return coverage_sources

    @staticmethod
    def coverage_start():
        if hasattr(common, "coverage"):
            return False
        _logger.info("Starting code coverage...")
        data_file = config.get("coverage_data_file") or "/tmp/.coverage"
        common.coverage = coverage.coverage(branch=True, data_file=data_file)
        common.coverage.exclude("(.*?)fields.(.*?)")
        common.coverage.start()
        return True

    @staticmethod
    def coverage_stop():
        if not hasattr(common, "coverage"):
            return False
        _logger.info("Stopping code coverage...")
        common.coverage.stop()
        common.coverage.save()
        coverage_result = tools.test_utils._get_coverage_result_file()
        sources = NewServices._get_coverage_sources()
        common.coverage.xml_report(
            morfs=sources,
            outfile=coverage_result,
            ignore_errors=True,
        )
        del common.coverage
        return True

    @staticmethod
    def run_tests(dbname, modules=None, with_coverage=True):
        init_test_enable = config.get("test_enable")
        config["test_enable"] = True
        threading.currentThread().dbname = dbname
        modules = tools.filter_modules_list(dbname, modules)
        tools.test_utils._remove_results_files()
        tools.run_unit_tests(dbname, modules)
        config["test_enable"] = init_test_enable
        return True

    @staticmethod
    def prepare_results_files():
        result = {"tests": {}}
        coverage_result_file = tools.test_utils._get_coverage_result_file()
        test_result_directory = tools.test_utils._get_test_result_directory()
        for file in os.listdir(test_result_directory):
            file_path = os.path.join(test_result_directory, file)
            with open(file_path, "r") as test:
                result["tests"][file] = test.read()
        with open(coverage_result_file, "r") as file:
            result["coverage"] = file.read()
        return result


native_dispatch = common.dispatch
additional_methods = [
    attr
    for attr in dir(NewServices)
    if not attr.startswith("_") and callable(getattr(NewServices, attr))
]


def new_dispatch(*args):
    method = args[0]
    if method in additional_methods:
        params = args[1]
        admin_passwd, params = params[0], params[1:]
        check_super(admin_passwd)
        return getattr(NewServices, method)(*params)
    return native_dispatch(*args)


common.dispatch = new_dispatch


@classmethod
def tearDownClass(cls):
    cls.cr.close()
    old_tearDownClass()


old_tearDownClass = BaseCase.tearDownClass
BaseCase.tearDownClass = tearDownClass
