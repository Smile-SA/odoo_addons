# -*- coding: utf-8 -*-
# (C) 2018 Smile (<http://www.smile.fr>)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import api
from odoo.addons.base.models.ir_cron import ir_cron

from ..tools import PerfLogger, profile

native_callback = ir_cron._callback


@api.model
def _callback(self, cron_name, server_action_id, job_id):
    logger = PerfLogger()
    logger.on_enter(self._cr, self._uid, '', 'ir.cron', '_callback')
    if logger.active:
        args = (job_id,)
        try:
            func = profile(native_callback)
            func(self, cron_name, server_action_id, job_id)
            logger.log_call(args)
        except Exception as e:
            logger.log_call(args, err=e)
            raise
        finally:
            logger.on_leave()
    else:
        logger.on_leave()
        native_callback(self, cron_name, server_action_id, job_id)


ir_cron._callback = _callback
