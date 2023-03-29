# -*- coding: utf-8 -*-

import importlib
import inspect
import itertools
import logging
import unittest

from odoo import addons


_logger = logging.getLogger(__name__)


def get_test_modules(module):
    """Return a list of module for the addons potentialy containing tests to
    feed unittest.TestLoader.loadTestsFromModule()"""
    # Try to import the module
    modpath = f"{addons.__name__}.{module}"
    try:
        mod = importlib.import_module(".tests", modpath)
    except Exception as e:
        # If module has no `tests` sub-module, no problem.
        if str(e) != "No module named tests":
            _logger.debug("Can not `import %s`.", module)
        return []

    return [
        mod_obj
        for name, mod_obj in inspect.getmembers(mod, inspect.ismodule)
        if name.startswith("test_")
    ]


def unwrap_suite(test):
    """
    Attempts to unpack testsuites (holding suites or cases) in order to
    generate a single stream of terminals (either test cases or customized
    test suites). These can then be checked for run/skip attributes
    individually.

    An alternative would be to use a variant of @unittest.skipIf with a state
    flag of some sort e.g. @unittest.skipIf(common.runstate != 'at_install'),
    but then things become weird with post_install as tests should *not* run
    by default there
    """
    if isinstance(test, unittest.TestCase):
        yield test
        return

    subtests = list(test)
    # custom test suite (no test cases)
    if not len(subtests):
        yield test
        return

    yield from itertools.chain.from_iterable(unwrap_suite(t) for t in subtests)
