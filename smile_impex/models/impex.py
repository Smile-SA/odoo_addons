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

from openerp import api, fields, models, registry, SUPERUSER_ID, _
from openerp.exceptions import Warning
from openerp.modules.registry import Registry

from openerp.addons.smile_log.tools import SmileDBLogger

from ..tools import s2human

_logger = logging.getLogger(__package__)


class IrModelImpexTemplate(models.AbstractModel):
    _name = 'ir.model.impex.template'
    _description = 'Import/Export Template'

    name = fields.Char(size=64, required=True)
    model_id = fields.Many2one('ir.model', 'Object', required=True, ondelete='cascade')
    method = fields.Char(size=64, required=True, help='Arguments can be passed through Method args '
                                                      'or received at import/export creation call')
    method_args = fields.Char(help="Arguments passed as a dictionary\nExample: {'code': '705000'}")
    cron_id = fields.Many2one('ir.cron', 'Scheduled Action')
    server_action_id = fields.Many2one('ir.actions.server', 'Server action')
    new_thread = fields.Boolean('New Thread', default=True)

    def _get_cron_vals(self):
        return {
            'name': self.name,
            'user_id': 1,
            'model': self._name,
            'args': '(%d, )' % self.id,
            'numbercall': -1,
        }

    @api.one
    def create_cron(self):
        if not self.cron_id:
            vals = self._get_cron_vals()
            cron_id = self.env['ir.cron'].create(vals)
            self.write({'cron_id': cron_id.id})
        return True

    def _get_server_action_vals(self, model_id):
        return {
            'name': self.name,
            'user_id': SUPERUSER_ID,
            'model_id': model_id,
            'state': 'code',
        }

    @api.one
    def create_server_action(self):
        if not self.server_action_id:
            model = self.env['ir.model'].search([('model', '=', self._name)], limit=1)
            if not model:  # Normally should not happen
                raise Warning(_('Please restart Odoo server'))
            vals = self._get_server_action_vals(model.id)
            self.server_action_id = self.env['ir.actions.server'].create(vals)
        return True

    @api.one
    def unlink_server_action(self):
        if self.client_action_id:
            raise Warning(_('Please remove client action before removing server action'))
        if self.server_action_id:
            self.server_action_id.unlink()
        return True


STATES = [
    ('running', 'Running'),
    ('done', 'Done'),
    ('exception', 'Exception'),
]


def state_cleaner(model):
    def decorator(method):
        def wrapper(self, cr, *args, **kwargs):
            res = method(self, cr, *args, **kwargs)
            if self.get(model._name):
                cr.execute("select relname from pg_class where relname='%s'" % model._table)
                if cr.rowcount:
                    impex_infos = self.get(model._name).search_read(cr, SUPERUSER_ID, [('state', '=', 'running')], ['pid'], order='id')
                    impex_ids = []
                    for impex in impex_infos:
                        if not psutil.pid_exists(impex['pid']):
                            impex_ids.append(impex['id'])
                    if impex_ids:
                        self.get(model._name).write(cr, SUPERUSER_ID, impex_ids, {'state': 'exception'})
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
        if not (self.from_date and self.to_date):
            self.time = 0
        else:
            timedelta = fields.Datetime.from_string(self.to_date) \
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
    state = fields.Selection(STATES, "State", readonly=True, required=True, default='running')
    pid = fields.Integer("Process Id", readonly=True)
    args = fields.Text('Arguments', readonly=True)

    @api.multi
    def write_with_new_cursor(self, vals):
        with registry(self._cr.dbname).cursor() as new_cr:
            return self.with_env(self.env(cr=new_cr)).write(vals)

    @api.multi
    def process(self):
        self._cr.commit()  # INFO: to access to import/export record via user interface
        res = []
        for record in self:
            if record.new_thread:
                cr, uid, context = self.env.args
                thread = Thread(target=self.pool[self._name]._process, args=(cr, uid, record.id, context))
                thread.start()
                res.append((record.id, True))
            else:
                res.append((record.id, record._process()))
        return res

    @api.multi
    def _process(self):
        self.ensure_one()
        logger = SmileDBLogger(self._cr.dbname, self._name, self.id, self._uid)
        self = self.with_context(logger=logger)
        self.write_with_new_cursor({'state': 'running', 'from_date': fields.Datetime.now(),
                                    'pid': os.getpid()})
        try:
            result = self._execute()
            self.write_with_new_cursor({'state': 'done', 'to_date': fields.Datetime.now()})
            if self.test_mode:
                self._cr.rollback()
            return result
        except Exception, e:
            logger.error(repr(e))
            try:
                self.write_with_new_cursor({'state': 'exception', 'to_date': fields.Datetime.now()})
            except:
                logger.warning("Cannot set import to exception")
            e.traceback = sys.exc_info()
            raise

    @api.multi
    def _execute(self):
        raise NotImplementedError
