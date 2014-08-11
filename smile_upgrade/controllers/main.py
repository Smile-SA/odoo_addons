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

from openerp.addons.web import http


@http.httprequest
def maintenance(self, req, **kwargs):
    return """
            <!DOCTYPE html>
            <html style="height: 100%%">
                <head>
                    <meta http-equiv="X-UA-Compatible" content="IE=edge,chrome=1"/>
                    <meta http-equiv="content-type" content="text/html; charset=utf-8" />
                    <title>OpenERP</title>
                    <link rel="shortcut icon" href="/web/static/src/img/favicon.ico" type="image/x-icon"/>
                    <link rel="stylesheet" href="/web/static/src/css/full.css" />
                    <link rel="stylesheet" href="/web/webclient/css">
                    <script type="text/javascript" src="/web/webclient/js"></script>
                </head>
                <body class="openerp openerp_webclient_container">
                    <div class="oe_login">
                        <div class="oe_login_bottom">
                            <p style="color:white">We are busy updating the application for you and will back soon shortly.</p>
                        </div>
                        <div class="oe_login_pane">
                            <div class="oe_login_logo">
                                <img src="/web/static/src/img/logo2.png">
                            </div>
                            <h1>We'll back soon.</h1>
                        </div>
                    </div>
                </body>
            </html>
        """
