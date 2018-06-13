# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2014 Smile (<http://www.smile.fr>).
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

import logging
import os
import psutil
import sys
from threading import Thread

from odoo import api, fields, models, SUPERUSER_ID
from odoo.tools.func import wraps

from odoo.addons.smile_log.tools import SmileDBLogger

from .impex_template import LOG_LEVELS
from ..tools import s2human, with_impex_cursor

_logger = logging.getLogger(__name__)


STATES = [
    ('running', 'Running'),
    ('done', 'Done'),
    ('exception', 'Exception'),
    ('killed', 'Killed'),
]


def state_cleaner(model):
    def decorator(method):
        @wraps(method)
        def wrapper(self, cr, *args, **kwargs):
            res = method(self, cr, *args, **kwargs)
            env = api.Environment(cr, SUPERUSER_ID, {})
            if model._name in env.registry.models:
                Model = env[model._name]
                cr.execute("select relname from pg_class "
                           "where relname='%s'" % model._table)
                if cr.rowcount:
                    impex_infos = Model.search_read(
                        [('state', '=', 'running')], ['pid'], order='id')
                    impex_ids = []
                    for impex in impex_infos:
                        if not psutil.pid_exists(impex['pid']):
                            impex_ids.append(impex['id'])
                    if impex_ids:
                        Model.browse(impex_ids).write({'state': 'killed'})
            return res
        return wrapper
    return decorator


class IrModelImpex(models.AbstractModel):
    _name = 'ir.model.impex'
    _description = 'Import/Export'
    _rec_name = 'create_date'
    _order = 'create_date desc'

    @api.one
    @api.depends('from_date', 'to_date')
    def _get_time(self):
        if not self.from_date:
            self.time = 0
        else:
            to_date = self.to_date or fields.Datetime.now()
            timedelta = fields.Datetime.from_string(to_date) \
                - fields.Datetime.from_string(self.from_date)
            self.time = timedelta.total_seconds()

    @api.one
    def _convert_time_to_human(self):
        self.time_human = s2human(self.time)

    create_date = fields.Datetime('Creation Date', readonly=True)
    create_uid = fields.Many2one('res.users', 'Creation User', readonly=True)
    from_date = fields.Datetime('Start date', readonly=True)
    to_date = fields.Datetime('End date', readonly=True)
    time = fields.Integer(compute='_get_time')
    time_human = fields.Char(
        'Time', compute='_convert_time_to_human', store=False)
    test_mode = fields.Boolean('Test Mode', readonly=True)
    new_thread = fields.Boolean('New Thread', readonly=True)
    state = fields.Selection(
        STATES, 'State', readonly=True, required=True, default='running')
    pid = fields.Integer('Process Id', readonly=True)
    args = fields.Text('Arguments', readonly=True)
    log_level = fields.Selection(LOG_LEVELS)
    log_returns = fields.Boolean('Log returns', readonly=True)
    returns = fields.Text('Returns', readonly=True)

    @api.multi
    def process(self):
        res = []
        for record in self:
            if record.new_thread or record.test_mode:
                thread = Thread(target=IrModelImpex._process_with_new_cursor,
                                args=(self,))
                thread.start()
                res.append((record.id, True))
            else:
                res.append((record.id, record._process()))
        return res

    @api.multi
    @with_impex_cursor(autocommit=False)
    def _process_with_new_cursor(self):
        self._process()

    @api.multi
    def _process(self):
        self.ensure_one()
        logger = SmileDBLogger(self._cr.dbname, self._name, self.id, self._uid)
        logger.setLevel(self.log_level)
        self = self.with_context(logger=logger)
        self.write({'state': 'running', 'from_date': fields.Datetime.now(),
                    'pid': os.getpid(), 'to_date': False})
        try:
            result = self._execute()
            vals = {'state': 'done', 'to_date': fields.Datetime.now()}
            if self.log_returns:
                vals['returns'] = repr(result)
            self.write(vals)
            if self.test_mode:
                self._cr.rollback()
            return result
        except Exception as e:
            logger.error(repr(e))
            try:
                self.write({
                    'state': 'exception',
                    'to_date': fields.Datetime.now(),
                })
            except Exception:
                logger.warning("Cannot set import to exception")
            e.traceback = sys.exc_info()
            raise

    @api.multi
    def _execute(self):
        raise NotImplementedError
