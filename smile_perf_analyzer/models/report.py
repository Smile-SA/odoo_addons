# -*- coding: utf-8 -*-
# (C) 2018 Smile (<http://www.smile.fr>)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import api
from odoo.addons.base.models.ir_actions_report import IrActionsReport

from ..tools import PerfLogger, profile

native_render_qweb_html = IrActionsReport.render_qweb_html


@api.model
def render_qweb_html(self, docids, data=None):
    logger = PerfLogger()
    logger.on_enter(self._cr, self._uid, '',
                    'ir.actions.report', 'render_qweb_html')
    args = (docids, data)
    try:
        func = profile(native_render_qweb_html)
        res = func(self, docids, data)
        logger.log_call(args, res=res)
        return res
    except Exception as e:
        logger.log_call(args, err=e)
        raise
    finally:
        logger.on_leave()


IrActionsReport.render_qweb_html = render_qweb_html
