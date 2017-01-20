# -*- encoding: utf-8 -*-

from openerp import tools
from openerp.addons.base.ir.ir_cron import ir_cron, _logger


native__acquire_job = ir_cron._acquire_job


@classmethod
def _acquire_job(cls, db_name):
    if tools.config.get('disable_cron', False):
        _logger.warning('Cron execution is not enabled. Remove `disable_cron = True` option to enable it.')
        return
    return native__acquire_job(db_name)


ir_cron._acquire_job = _acquire_job
