# -*- coding: utf-8 -*-

import openerp
from openerp.osv.orm import except_orm
from openerp.service import model

from ..tools import Logger, profile


def execute_cr(cr, uid, obj, method, *args, **kw):
    object = openerp.registry(cr.dbname).get(obj)
    if object is None:
        raise except_orm('Object Error', "Object %s doesn't exist" % obj)
    logger = Logger()
    logger.on_enter(obj, method)
    try:
        func = profile(getattr(object, method))
        res = func(cr, uid, *args, **kw)
        logger.log_call(args, kw, res)
        return res
    finally:
        logger.on_leave()


model.execute_cr = execute_cr
