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

import importlib
import inspect
import logging
import os
import types
import yaml

from openerp import addons, api, models

_logger = logging.getLogger(__package__)


class IrModuleModule(models.Model):
    _inherit = 'ir.module.module'

    @staticmethod
    def _get_yaml_test_files(module_name):
        """Returns the list of the paths indicated in 'test' of module manifest.

        @return: dict
        """
        test_files_by_module_path = {}
        if hasattr(addons, module_name):
            module = getattr(addons, module_name)
            module_path = module.__path__[0]
            file_path = os.path.join(module_path, '__openerp__.py')
            if not os.path.exists(file_path):
                _logger.error("No such file: %s", file_path)
            with open(file_path) as f:
                tests = eval(f.read()).get('test')
                if tests:
                    test_files_by_module_path[module_path] = tests
        return test_files_by_module_path

    @staticmethod
    def _get_yaml_test_comments(test_files):
        """Returns a list of tuple (basename of the file, path of the file, list of comments of the file).

        @return: list
        """
        res = []
        for module_path in test_files:
            module = os.path.basename(module_path)
            for file_path in test_files[module_path]:
                fp = os.path.join(module_path, file_path.replace('/', os.path.sep))
                if not os.path.exists(fp):
                    _logger.error("No such file: %s", fp)
                    continue
                with open(fp) as f_obj:
                    root, ext = os.path.splitext(f_obj.name)
                    if ext == '.yml':
                        comments = []
                        for node in yaml.load(f_obj.read()):
                            if isinstance(node, types.StringTypes):
                                comments.append(node)
                        res.append((os.path.basename(root), os.path.join(module, file_path), comments))
        return res

    @staticmethod
    def get_test_modules(module):
        """
        Returns the list of files starting by "test_" inside a module.
        Search recursively inside tests directory, so tests can be places inside subdirectories.

        @param module: module name (str)
        @return: list
        """
        def inspect_module(mod):
            result = []
            for name, mod_obj in inspect.getmembers(mod, inspect.ismodule):
                if name.startswith('test_'):
                    result.append(mod_obj)
                else:
                    result += inspect_module(mod_obj)
            return result

        modpath = 'openerp.addons.' + module
        try:
            mod = importlib.import_module('.tests', modpath)
        except Exception, e:
            if str(e) != 'No module named tests':
                _logger.exception('Can not `import %s`.', module)
            return []
        return inspect_module(mod)

    @staticmethod
    def _get_unit_test_comments(module_name):
        """Returns a list of tuple (basename of the file, path of the file, list of comments of the file).

        @return: list
        """
        res = []

        module_tests = IrModuleModule.get_test_modules(module_name)
        for module_test in module_tests:
            module_test_file = module_test.__file__
            if module_test_file.endswith('.pyc'):
                module_test_file = module_test_file[:-1]  # convert extension from .pyc to .py
            root, ext = os.path.splitext(os.path.basename(module_test_file))
            module_classes = [module_test.__getattribute__(attr) for attr in module_test.__dict__
                              if isinstance(module_test.__getattribute__(attr), type)]
            for module_class in module_classes:
                comments = []
                test_methods = [module_class.__dict__[attr] for attr in module_class.__dict__
                                if callable(module_class.__dict__[attr]) and attr.startswith('test')]
                if not test_methods:
                    continue
                if module_class.__dict__['__doc__']:
                    comments.append(module_class.__dict__['__doc__'])  # class docstring
                for test_method in sorted(test_methods, lambda x, y: cmp(x.__name__, y.__name__)):
                    comment = '%s:\n%s' % (test_method.__name__, test_method.__doc__ or '')  # method name and docstring
                    comments.append(comment)
                res.append((root, module_test_file, comments))

        return res

    @api.multi
    def get_tests(self):
        """Returns the tests documentation of each module.
            [(module_name, test_list), ...]

        @return: list
        """
        tests_by_module = {}
        for module in self:
            tests = []
            # YAML tests
            test_files = IrModuleModule._get_yaml_test_files(module.name)
            tests.extend(IrModuleModule._get_yaml_test_comments(test_files))
            # Unit tests
            tests.extend(IrModuleModule._get_unit_test_comments(module.name))
            if tests:
                # Add tests for this module
                tests_by_module[module.name] = tests
        return sorted([(module_name, tests_by_module[module_name]) for module_name in tests_by_module], lambda x, y: cmp(x[0], y[0]))
