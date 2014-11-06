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

import os

from openerp import api, models, tools
from openerp.modules.module import load_information_from_description_file


class Module(models.Model):
    _inherit = 'ir.module.module'

    @api.one
    def load_data(self, kind='demo', mode='update', noupdate=False):
        cr = self._cr
        info = load_information_from_description_file(self.name)
        for filename in info.get(kind, []):
            _, ext = os.path.splitext(filename)
            pathname = os.path.join(self.name, filename)
            with tools.file_open(pathname) as fp:
                if ext == '.sql':
                    tools.convert_sql_import(cr, fp)
                elif ext == '.csv':
                    tools.convert_csv_import(cr, self.name, pathname, fp.read(), idref=None, mode=mode, noupdate=noupdate)
                elif ext == '.yml':
                    tools.convert_yaml_import(cr, self.name, fp, kind=kind, idref=None, mode=mode, noupdate=noupdate)
                elif ext == '.xml':
                    tools.convert_xml_import(cr, self.name, fp, idref=None, mode=mode, noupdate=noupdate)
        return True
