# -*- coding: utf-8 -*-

import xmlrpclib

from openerp.exceptions import except_orm
from openerp.tools import ustr


def get_exception_message(e):
    e = e or ''
    if isinstance(e, basestring):
        return ustr(e)
    if isinstance(e, except_orm):
        return ustr(e.value)
    if isinstance(e, xmlrpclib.Fault):
        return ustr(e.faultString)
    return ustr(e.message)
