# -*- encoding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2014 Smile (<http://www.smile.fr>). All Rights Reserved
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

import logging
import os

from openerp import api, models, modules, tools
from openerp.modules.module import load_information_from_description_file

_logger = logging.getLogger(__name__)


class Module(models.Model):
    _inherit = 'ir.module.module'

    @api.multi
    def _get_all_dependencies(self):
        all_dependencies = self.browse(self.ids)
        parent_modules = self.browse(self.ids)
        while parent_modules:
            dependencies = self.browse()
            for module in parent_modules:
                for dependency in module.dependencies_id:
                    dependencies |= dependency.depend_id
            parent_modules = dependencies - all_dependencies
            all_dependencies |= parent_modules
        return all_dependencies

    @api.multi
    def load_data(self, kind='demo', mode='update', noupdate=False):
        module_names = [module.name for module in self]
        module_list = [module.name for module in self._get_all_dependencies()]
        graph = modules.graph.Graph()
        graph.add_modules(self._cr, module_list)
        for module in graph:
            if module.name in module_names:
                self._load_data(module.name, kind, mode, noupdate)

    @api.model
    def _load_data(self, module_name, kind='demo', mode='update', noupdate=False):
        cr = self._cr
        info = load_information_from_description_file(module_name)
        for filename in info.get(kind, []):
            _logger.info('loading %s/%s...' % (module_name, filename))
            _, ext = os.path.splitext(filename)
            pathname = os.path.join(module_name, filename)
            with tools.file_open(pathname) as fp:
                if ext == '.sql':
                    tools.convert_sql_import(cr, fp)
                elif ext == '.csv':
                    tools.convert_csv_import(cr, module_name, pathname, fp.read(), idref=None, mode=mode, noupdate=noupdate)
                elif ext == '.yml':
                    tools.convert_yaml_import(cr, module_name, fp, kind=kind, idref=None, mode=mode, noupdate=noupdate)
                elif ext == '.xml':
                    tools.convert_xml_import(cr, module_name, fp, idref=None, mode=mode, noupdate=noupdate)
        return True
