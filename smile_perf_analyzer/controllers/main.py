# -*- coding: utf-8 -*-

from openerp.addons.web.controllers.main import DataSet
from openerp.http import request

from ..tools import PerfLogger, profile


def _call_kw(self, model, method, args, kwargs):
    if method.startswith('_'):
        raise Exception("Access Denied: Underscore prefixed methods cannot be remotely called")
    logger = PerfLogger()
    logger.on_enter(model, method)
    try:
        func = profile(getattr(request.registry.get(model), method))
        res = func(request.cr, request.uid, *args, **kwargs)
        logger.log_call(args, kwargs, res)
        return res
    finally:
        logger.on_leave()


DataSet._call_kw = _call_kw
