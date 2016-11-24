# -*- coding: utf-8 -*-

import xmlrpclib

from odoo import exceptions, tools


def get_exception_message(e):
    if isinstance(e, exceptions.except_orm):
        msg = e.value or e.name
    elif isinstance(e, xmlrpclib.Fault):
        msg = e.faultString
    else:
        msg = e.message
    return tools.ustr(msg or e)
