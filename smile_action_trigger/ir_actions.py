# -*- encoding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution    
#    Copyright (C) 2010 Smile (<http://www.smile.fr>). All Rights Reserved
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

from osv import fields, osv

class actions_server(osv.osv):
    _inherit = 'ir.actions.server'

    _columns = {
        'active': fields.boolean("Active"),
        'run_once': fields.boolean("Run once for all instances", help="Works only from trigger rules. If checked, the variable object is a browse record list"),
        'user_id': fields.many2one('res.users', "User", help="If empty, the action is executed by the current user"),
    }

    _defaults = {
        'active': lambda * a: True,
        'run_once': lambda * a: False,
    }
actions_server()
