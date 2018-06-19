# -*- coding: utf-8 -*-

from docker.errors import APIError
import logging
import xmlrpclib

from odoo import exceptions, tools
from odoo.tools.func import wraps

_logger = logging.getLogger(__name__)


def get_exception_message(e):
    msg = None
    if isinstance(e, exceptions.except_orm):
        msg = e.value or e.name
    elif isinstance(e, xmlrpclib.Fault):
        msg = e.faultString
    elif isinstance(e, APIError):
        msg = str(e)
    else:
        msg = e.message
    return tools.ustr(msg or e)


def secure(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            _logger.error('%s failed: %s' % (func.__name__, e))
    return wrapper
