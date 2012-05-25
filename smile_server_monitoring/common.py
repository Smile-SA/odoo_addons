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

import sys
import imp
import gc

from service.web_services import common

native_dispatch = common.dispatch


def load_native_resource_module():
    """ Useful to bypass server/bin/addons/resource module of OpenERP ... """
    if 'resource' in sys.modules and hasattr(sys.modules['resource'], 'getrusage'):
        return

    fp = None
    for path in sys.path:
        try:
            fp, pathname, description = imp.find_module('resource', [path])
            resource_module = imp.load_module('resource', fp, pathname, description)
            if hasattr(resource_module, 'getrusage'):
                #Ok, its the native resource module
                return
        except ImportError:
            pass
        finally:
            # close fp if necessary.
            if fp:
                fp.close()

def get_memory():
    load_native_resource_module()
    if 'resource' in sys.modules:
        resource = sys.modules['resource']
        return "%s kb" % (resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,)
    else:
        return 'Unknown'

def gc_collect(generation=None):
    if generation:
        return gc.collect(generation)
    else:
        return gc.collect()

def gc_garbage():
    return repr(gc.garbage)

def get_count():
    return gc.get_count()

def new_dispatch(self, method, auth, params):
    if method == 'get_memory':
        return get_memory()
    elif method == 'gc_collect':
        return gc_collect(*params)
    elif method == 'gc_garbage':
        return gc_garbage()
    elif method == 'gc_get_count':
        return get_count()
    else:
        return native_dispatch(self, method, auth, params)

common.dispatch = new_dispatch
