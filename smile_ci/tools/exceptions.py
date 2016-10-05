# -*- coding: utf-8 -*-

import xmlrpclib

from odoo import exceptions, tools


def get_exception_message(e):
    if isinstance(e, exceptions.except_orm):
        return tools.ustr(e.value)
    if isinstance(e, xmlrpclib.Fault):
        return tools.ustr(e.faultString)
    return tools.ustr(e.message)
