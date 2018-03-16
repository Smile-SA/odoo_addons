# -*- coding: utf-8 -*-

from openerp.addons.base.ir.ir_cron import ir_cron
from openerp.tools.safe_eval import safe_eval

from ..tools import PerfLogger, profile

native_callback = ir_cron._callback


def _callback(self, cr, uid, model_name, method_name, args, job_id):
    logger = PerfLogger()
    logger.on_enter(cr, uid, '', model_name, method_name)
    if logger.active and logger.log_cron:
        try:
            func = profile(native_callback)
            func(self, cr, uid, model_name, method_name, args, job_id)
            logger.log_call(args and safe_eval(args) or None)
        except Exception, e:
            logger.log_call(args and safe_eval(args) or None, err=e)
            raise
        finally:
            logger.on_leave()
    else:
        logger.on_leave()
        native_callback(self, cr, uid, model_name, method_name, args, job_id)

ir_cron._callback = _callback
