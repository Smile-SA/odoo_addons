# -*- coding: utf-8 -*-
# (C) 2020 Smile (<http://www.smile.fr>)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import api, fields, models, SUPERUSER_ID, _
from odoo.exceptions import AccessError


class Base(models.AbstractModel):
    _inherit = "base"

    @api.model
    def check_access_rights(self, operation, raise_exception=True):
        def raise_access_exception(date_from=None, date_to=None):
            if raise_exception:
                msg = _("You can not %s this document (%s)")
                params = [_(operation), self._name]
                if date_from:
                    msg += _(" from %s")
                    params.append(date_from)
                if date_to:
                    msg += _(" to %s")
                    params.append(date_to)
                raise AccessError(msg % tuple(params))
            return False

        if self._uid == SUPERUSER_ID:
            return True
        if self._name != 'res.users.log' and \
                operation in ('create', 'write', 'unlink'):
            today = fields.Date.today()
            date_start, date_stop = self.env['res.users'].get_readonly_dates()
            if date_start and date_stop:
                if date_start <= today <= date_stop:
                    return raise_access_exception(date_start, date_stop)
            elif date_start:  # Only date_start
                if today >= date_start:
                    return raise_access_exception(date_start)
            elif date_stop:  # Only date_stop
                if today <= date_stop:
                    return raise_access_exception(date_to=date_stop)
        return super(Base, self).check_access_rights(
            operation, raise_exception)
