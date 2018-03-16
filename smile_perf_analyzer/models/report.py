# -*- coding: utf-8 -*-

from odoo import report

from ..tools import PerfLogger, profile

native_render_report = report.render_report


def render_report(cr, uid, ids, name, data, context=None):
    logger = PerfLogger()
    logger.on_enter(cr, uid, '/xmlrpc/report', '', 'render_report')
    try:
        res = profile(native_render_report)(cr, uid, ids, name, data, context)
        logger.log_call((ids, name, data, context), res=res)
        return res
    except Exception, e:
        logger.log_call((ids, name, data, context), err=e)
        raise
    finally:
        logger.on_leave()

report.render_report = render_report
