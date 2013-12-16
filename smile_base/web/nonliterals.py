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

from openerp.addons.web.common.nonliterals import SuperDict

native_getitem = SuperDict.__getitem__


class ParentDict(object):

    def __init__(self, d):
        self.d = d

    def __getattr__(self, name):
        return self.d.get(name, False)


def new_getitem(self, key):
    tmp = native_getitem(self, key)
    if key == 'parent' and isinstance(tmp, dict):
        tmp = ParentDict(tmp)
    return tmp


SuperDict.__getitem__ = new_getitem
