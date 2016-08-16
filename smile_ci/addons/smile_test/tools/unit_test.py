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

import itertools
import logging
import re
import sys
import unittest

_logger = logging.getLogger(__name__)


def get_test_modules(module):
    """ Return a list of module for the addons potentialy containing tests to
    feed unittest2.TestLoader.loadTestsFromModule() """
    # Try to import the module
    module = 'openerp.addons.' + module + '.tests'
    try:
        __import__(module)
    except Exception, e:
        # If module has no `tests` sub-module, no problem.
        if str(e) != 'No module named tests':
            _logger.exception('Can not `import %s`.', module)
        return []

    # include submodules too
    result = [mod_obj for name, mod_obj in sys.modules.iteritems()
              if mod_obj  # mod_obj can be None
              if name.startswith(module)
              if re.search(r'test_\w+$', name)]
    return result


def unwrap_suite(test):
    """
    Attempts to unpack testsuites (holding suites or cases) in order to
    generate a single stream of terminals (either test cases or customized
    test suites). These can then be checked for run/skip attributes
    individually.

    An alternative would be to use a variant of @unittest2.skipIf with a state
    flag of some sort e.g. @unittest2.skipIf(common.runstate != 'at_install'),
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

    for item in itertools.chain.from_iterable(
            itertools.imap(unwrap_suite, subtests)):
        yield item
