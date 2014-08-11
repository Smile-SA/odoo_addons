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

from openerp import http
from openerp.addons.web.controllers.main import Home

routes = [r.rule for r in http.root.nodb_routing_map.iter_rules() if r.endpoint.method.routing['type'] == 'http']


class Maintenance(Home):

    @http.route(routes, type='http', auth="none")
    def index(self, **kwargs):
        return """
            <!DOCTYPE html>
            <html style="height: 100%%">
                <head>
                    <meta http-equiv="X-UA-Compatible" content="IE=edge,chrome=1"/>
                    <meta http-equiv="content-type" content="text/html; charset=utf-8"/>
                    <title>Odoo</title>
                    <link rel="shortcut icon" href="/web/static/src/img/favicon.ico" type="image/x-icon"/>
                    <link rel="stylesheet" href="/web/static/src/css/full.css"/>
                    <link href="/web/static/src/css/base.css" rel="stylesheet"/>
                    <link href="/web/static/lib/bootstrap/css/bootstrap.css" rel="stylesheet"/>
                </head>
                <body class="oe_single_form">
                    <div class="oe_single_form_container modal-content">
                        <center>
                            <img src="/web/static/src/img/logo2.png">
                            <h2>We'll back soon.</h2>
                            <p>We are busy updating the application for you and will back soon shortly.</p>
                        </center>
                    </div>
                </body>
            </html>
            """
