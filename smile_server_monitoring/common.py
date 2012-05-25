# -*- encoding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution    
#    Copyright (C) 2012 Smile (<http://www.smile.fr>). All Rights Reserved
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


from service.web_services import common

native_dispatch = common.dispatch


def get_native_resource_module():
    """ Useful to bypass server/bin/addons/resource module of OpenERP ... """
    import sys
    import imp
    fp = None
    for path in sys.path:
        try:
            fp, pathname, description = imp.find_module('resource', [path])
            resource_module = imp.load_module('resource', fp, pathname, description)
            if hasattr(resource_module, 'getrusage'):
                #Ok, its the native resource module
                return resource_module
        except ImportError:
            pass
        finally:
            # Since we may exit via an exception, close fp explicitly.
            if fp:
                fp.close()
    return None


def new_dispatch(self, method, auth, params):
    if method == 'get_memory':
        resource = get_native_resource_module()
        if resource:
            return "%s kb" % (resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,)
        else:
            return False
    else:
        return native_dispatch(self, method, auth, params)

common.dispatch = new_dispatch
