# -*- coding: utf-8 -*-

import datetime
from dateutil.relativedelta import relativedelta
import time

from odoo.tests.common import TransactionCase


class TestActWindow(TransactionCase):
    def _get_models_to_ignore(self):
        return []

    def test_act_window(self):
        """I test all search and first reads for all act_windows."""
        errors = []
        # Only test act_window from menus: others might require active_ids
        menu_infos = self.env["ir.ui.menu"].search_read([], ["action"])
        user_context = dict(self.env["res.users"].context_get())
        actions = [
            info["action"].split(",") for info in menu_infos if info["action"]
        ]
        act_window_ids = list(
            {
                int(res_id)
                for model, res_id in actions
                if model == "ir.actions.act_window"
            }
        )
        # context built as in webclient
        user_context |= {
            "active_model": "",
            "active_id": False,
            "active_ids": [],
            "uid": self.env.user.id,
            "user": self.env.user,
            "time": time,
            "datetime": datetime,
            "relativedelta": relativedelta,
            "current_date": time.strftime("%Y-%m-%d"),
        }
        act_windows = (
            self.env["ir.actions.act_window"]
            .browse(act_window_ids)
            .filtered(
                lambda act_window: act_window.res_model
                not in self._get_models_to_ignore()
            )
        )
        for act_window in act_windows:
            model = act_window.res_model
            buf_context = user_context.copy()
            buf_context["context"] = user_context.copy()
            try:
                with self.env.cr.savepoint():
                    test_context = (
                        eval(
                            act_window.context
                            and act_window.context.strip()
                            or "{}",
                            buf_context,
                        )
                        or buf_context
                    )
                    test_domain = (
                        eval(
                            act_window.domain
                            and act_window.domain.strip()
                            or "[]",
                            buf_context,
                        )
                        or []
                    )
                    test_limit = (
                        int(act_window.limit) if act_window.limit else None
                    )
                    self.env[model].with_context(**test_context).search_read(
                        test_domain, offset=0, limit=test_limit
                    )
            except Exception as e:
                err_info = (
                    act_window.name,
                    act_window.res_model,
                    act_window.domain,
                    act_window.limit,
                    act_window.context,
                    repr(e),
                )
                errors.append(err_info)
        err_details = "\n".join(
            "(%s, %s, %s, %s, %s): %s" % error for error in errors
        )
        error_msg = (
            "Error in search/read for act_window/model "
            "and error:\n%s" % err_details
        )
        self.assertEqual(len(errors), 0, error_msg)
