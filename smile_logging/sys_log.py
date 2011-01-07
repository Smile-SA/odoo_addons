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

from osv import osv, fields

class smile_log(osv.osv):
    _name = 'sys.log'

    _columns = {
        'name': fields.char('Name', size=128),
        'create_date': fields.datetime('Create Date', readonly=True),
        'create_uid': fields.many2one('res.users', 'User', readonly=True),
        'levelno': fields.integer('Level Number'),
        'levelname': fields.char('Level Name', size=64),
        'lineno': fields.integer('Line Number'),
        'module': fields.char('Module', size=128),
        'msecs': fields.float('Length'),
        'pathname': fields.char('pathname', size=255),
        'message': fields.text('Message'),
        'failed': fields.boolean('Failed'),
        'exception': fields.text('exception'),
    }
smile_log()
