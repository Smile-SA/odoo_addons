# -*- coding: utf-8 -*-

from odoo import api
from odoo.addons.base.ir.ir_cron import ir_cron
from odoo.tools.safe_eval import safe_eval

from ..tools import PerfLogger, profile

native_callback = ir_cron._callback


@api.model
def _callback(self, model_name, method_name, args, job_id):
    logger = PerfLogger()
    logger.on_enter(self._cr, self._uid, '', model_name, method_name)
    if logger.active and logger.log_cron:
        try:
            func = profile(native_callback)
            func(self, model_name, method_name, args, job_id)
            logger.log_call(args and safe_eval(args) or None)
        except Exception, e:
            logger.log_call(args and safe_eval(args) or None, err=e)
            raise
        finally:
            logger.on_leave()
    else:
        logger.on_leave()
        native_callback(self, model_name, method_name, args, job_id)

ir_cron._callback = _callback
