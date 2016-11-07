# -*- encoding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2011 Smile (<http://www.smile.fr>). All Rights Reserved
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

import werkzeug

from odoo import models
from odoo.http import request


class Http(models.AbstractModel):
    _inherit = 'ir.http'

    @classmethod
    def _website_enabled(cls):
        try:
            func, arguments = cls._find_handler()
            return func.routing.get('website', False)
        except werkzeug.exceptions.NotFound:
            return True

    @classmethod
    def _dispatch(cls):
        if cls._website_enabled():
            if not request.uid and request.context.get('uid'):
                user = request.env['res.users'].browse(request.context['uid'])
            else:
                user = request.env.user
            if user:
                request.uid = user.login_as_user_id.id or user.id
        return super(Http, cls)._dispatch()
