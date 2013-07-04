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

from openerp.utils import cache, rpc

@cache.memoize(1000)
def __can_create(model, uid):
    proxy = rpc.RPCProxy('ir.model.access')
    try:
        return proxy.check(model, 'create')
    except:
        pass
    return False

def can_create(model):
    return __can_create(model, uid=rpc.session.uid)

cache.can_create = can_create

@cache.memoize(1000)
def __can_unlink(model, uid):
    proxy = rpc.RPCProxy('ir.model.access')
    try:
        return proxy.check(model, 'unlink')
    except:
        pass
    return False

def can_unlink(model):
    return __can_unlink(model, uid=rpc.session.uid)

cache.can_unlink = can_unlink

