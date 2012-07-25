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

import cherrypy

from openerp.utils import cache, rpc


def fields_view_get(model, view_id, view_type, context, hastoolbar=False, hassubmenu=False):
    if model in cherrypy.config.get('cache.exceptions', '').split(', '):
        return rpc.RPCProxy(model).fields_view_get(view_id, view_type, context, hastoolbar, hassubmenu)
    return __fields_view_get(model, view_id, view_type, context, hastoolbar=hastoolbar, hassubmenu=hassubmenu, uid=rpc.session.uid)

cache.fields_view_get = fields_view_get


def fields_get(model, fields, context):
    if model in cherrypy.config.get('cache.exceptions', '').split(', '):
        return rpc.RPCProxy(model).fields_get(fields, context)
    return __fields_get(model, fields, context, uid=rpc.session.uid)

cache.fields_get = fields_get
