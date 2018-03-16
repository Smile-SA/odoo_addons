# -*- coding: utf-8 -*-

from odoo import service

from ..tools import PerfLogger, profile

native_execute_cr = service.model.execute_cr


def execute_cr(cr, uid, obj, method, *args, **kw):
    logger = PerfLogger()
    logger.on_enter(cr, uid, '/xmlrpc/object', obj, method)
    try:
        res = profile(native_execute_cr)(cr, uid, obj, method, *args, **kw)
        logger.log_call(args, kw, res)
        return res
    except Exception, e:
        logger.log_call(args, kw, err=e)
        raise
    finally:
        logger.on_leave()

service.model.execute_cr = execute_cr
