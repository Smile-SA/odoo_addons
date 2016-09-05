# -*- encoding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2011 Smile (<http://www.smile.fr>). All Rights Reserved
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

import os
import time

from odoo import api, models, fields


class SmileLog(models.Model):
    _name = 'smile.log'
    _description = 'Smile Logs'
    _rec_name = 'message'
    _log_access = False
    _order = 'log_date desc'

    @api.one
    @api.depends('log_uid')
    def _get_user_name(self):
        user = self.env['res.users'].browse(self.log_uid)
        if user.exists():
            self.log_user_name = "%s [%s]" % (user.name, self.log_uid)
        else:
            self.log_user_name = "[%s]" % self.log_uid

    @api.one
    @api.depends('res_id')
    def _get_res_name(self):
        res = self.env[self.model_name].browse(self.res_id)
        infos = res.name_get()
        if infos:
            self.log_res_name = infos[0][1]

    log_date = fields.Datetime('Date', readonly=True)
    log_uid = fields.Integer('User', readonly=True)
    log_user_name = fields.Char(string='User', size=256, compute='_get_user_name')
    log_res_name = fields.Char(string='Ressource name', size=256, compute='_get_res_name')
    model_name = fields.Char('Model name', size=64, readonly=True, index=True)
    res_id = fields.Integer('Ressource id', readonly=True, group_operator="count", index=True)
    pid = fields.Integer(readonly=True, group_operator="count")
    level = fields.Char(size=16, readonly=True)
    message = fields.Text('Message', readonly=True)

    @api.model
    def archive_and_delete_old_logs(self, nb_days=90, archive_path=''):
        # Thanks to transaction isolation, the COPY and DELETE will find the same smile_log records
        if archive_path:
            file_name = time.strftime("%Y%m%d_%H%M%S.log.csv")
            file_path = os.path.join(archive_path, file_name)
            self.env.cr.execute("""COPY (SELECT * FROM smile_log
            WHERE log_date + interval'%s days' < NOW() at time zone 'UTC')
            TO %s
            WITH (FORMAT csv, ENCODING utf8)""", (nb_days, file_path,))
        self.env.cr.execute("DELETE FROM smile_log WHERE log_date + interval '%s days' < NOW() at time zone 'UTC'",
                            (nb_days,))
        return True
