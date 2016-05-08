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
import psycopg2
import sys
from threading import Thread

from openerp import api, fields, models, SUPERUSER_ID, _
from openerp.exceptions import UserError
from openerp.tools.func import wraps

from openerp.addons.smile_log.tools import SmileDBLogger

from ..tools import s2human, with_impex_cursor

LOG_LEVELS = [
    (0, 'NOTSET'),
    (10, 'DEBUG'),
    (20, 'INFO'),
    (30, 'WARNING'),
    (40, 'ERROR'),
    (50, 'CRITICAL'),
]

_logger = logging.getLogger(__package__)


class IrModelImpexTemplate(models.AbstractModel):
    _name = 'ir.model.impex.template'
    _description = 'Import/Export Template'

    name = fields.Char(size=64, required=True)
    model_id = fields.Many2one('ir.model', 'Model', required=True, ondelete='cascade')
    method = fields.Char(size=64, required=True, help='Arguments can be passed through Method args '
                                                      'or received at import/export creation call')
    method_args = fields.Char(help="Arguments passed as a dictionary\nExample: {'code': '705000'}")
    cron_id = fields.Many2one('ir.cron', 'Scheduled Action', copy=False)
    server_action_id = fields.Many2one('ir.actions.server', 'Server action', copy=False)
    new_thread = fields.Boolean(default=True)
    log_level = fields.Selection(LOG_LEVELS, default=20, required=True)
    log_entry_args = fields.Boolean('Log entry arguments', default=True)
    log_returns = fields.Boolean('Log returns')
    one_at_a_time = fields.Boolean()

    @api.multi
    def _try_lock(self, warning=None):
        self = self.filtered(lambda tmpl: tmpl.one_at_a_time)
        if not self:
            return
        try:
            self._cr.execute("""SELECT id FROM "%s" WHERE id IN %%s FOR UPDATE NOWAIT""" % self._table,
                             (tuple(self.ids),), log_exceptions=False)
        except psycopg2.OperationalError:
            self._cr.rollback()  # INFO: Early rollback to allow translations to work for the user feedback
            if warning:
                raise UserError(warning)
            raise

    def _get_cron_vals(self, **kwargs):
        vals = {
            'name': self.name,
            'user_id': 1,
            'model': self._name,
            'args': '(%d, )' % self.id,
            'numbercall': -1,
        }
        vals.update(kwargs)
        return vals

    @api.one
    def create_cron(self, **kwargs):
        if not self.cron_id:
            vals = self._get_cron_vals(**kwargs)
            cron_id = self.env['ir.cron'].create(vals)
            self.write({'cron_id': cron_id.id})
        return True

    def _get_server_action_vals(self, model_id, **kwargs):
        vals = {
            'name': self.name,
            'user_id': SUPERUSER_ID,
            'model_id': model_id,
            'state': 'code',
        }
        vals.update(kwargs)
        return vals

    @api.one
    def create_server_action(self, **kwargs):
        if not self.server_action_id:
            model = self.env['ir.model'].search([('model', '=', self._name)], limit=1)
            if not model:  # Normally should not happen
                raise UserError(_('Please restart Odoo server'))
            vals = self._get_server_action_vals(model.id, **kwargs)
            self.server_action_id = self.env['ir.actions.server'].create(vals)
        return True

    @api.one
    def unlink_server_action(self):
        if self.client_action_id:
            raise UserError(_('Please remove client action before removing server action'))
        if self.server_action_id:
            self.server_action_id.unlink()
        return True


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
            model_obj = self.get(model._name)
            if model_obj:
                cr.execute("select relname from pg_class where relname='%s'" % model._table)
                if cr.rowcount:
                    impex_infos = model_obj.search_read(cr, SUPERUSER_ID, [('state', '=', 'running')],
                                                        ['pid'], order='id')
                    impex_ids = []
                    for impex in impex_infos:
                        if not psutil.pid_exists(impex['pid']):
                            impex_ids.append(impex['id'])
                    if impex_ids:
                        model_obj.write(cr, SUPERUSER_ID, impex_ids, {'state': 'killed'})
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
    time_human = fields.Char('Time', compute='_convert_time_to_human', store=False)
    test_mode = fields.Boolean('Test Mode', readonly=True)
    new_thread = fields.Boolean('New Thread', readonly=True)
    state = fields.Selection(STATES, 'State', readonly=True, required=True, default='running')
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
                thread = Thread(target=IrModelImpex._process_with_new_cursor, args=(self,))
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
        except Exception, e:
            logger.error(repr(e))
            try:
                self.write({'state': 'exception', 'to_date': fields.Datetime.now()})
            except:
                logger.warning("Cannot set import to exception")
            e.traceback = sys.exc_info()
            raise

    @api.multi
    def _execute(self):
        raise NotImplementedError
