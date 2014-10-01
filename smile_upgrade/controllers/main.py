# -*- encoding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2013 Smile (<http://www.smile.fr>). All Rights Reserved
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

import jinja2
import os

from openerp import http
from openerp.addons.web.controllers.main import Home

routes = [r.rule for r in http.root.nodb_routing_map.iter_rules() if r.endpoint.method.routing['type'] == 'http']


class Maintenance(Home):

    @http.route(routes, type='http', auth="none")
    def maintenance(self, **kwargs):
        path = os.path.realpath(os.path.join(os.path.dirname(__file__), '..', 'views'))
        loader = jinja2.FileSystemLoader(path)
        env = jinja2.Environment(loader=loader, autoescape=True)
        return env.get_template("maintenance.html").render()
