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
from threading import Thread

from openerp import api, fields, models, SUPERUSER_ID, _
from openerp.exceptions import Warning
from openerp.modules.registry import Registry

from openerp.addons.smile_log.tools import SmileDBLogger

from ..tools.api import cursor, with_new_cursor
from ..tools.misc import s2human

_logger = logging.getLogger(__package__)


class IrModelImpexTemplate(models.AbstractModel):
    _name = 'ir.model.impex.template'
    _description = 'Import/Export Template'

    name = fields.Char(size=64, required=True)
    model_id = fields.Many2one('ir.model', 'Object', required=True, ondelete='cascade')
    method = fields.Char(size=64, required=True, help='Arguments can be passed through Method args')
    method_args = fields.Char(help="Arguments passed as a dictionary\nExample: {'code': '705000'}")
    cron_id = fields.Many2one('ir.cron', 'Scheduled Action')
    server_action_id = fields.Many2one('ir.actions.server', 'Server action')

    def _get_cron_vals(self):
        return {
            'name': self.name,
            'user_id': 1,
            'model': self._name,
            'args': '(%d, )' % self.id,
            'numbercall':-1,
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
        def wrapper(self, cr, module):
            res = method(self, cr, module)
            if self.get(model._name):
                cr.execute("select relname from pg_class where relname='%s'" % model._table)
                if cr.rowcount:
                    impex_ids = self.get(model._name).search(cr, 1, [('state', '=', 'running')])
                    if impex_ids:
                        self.get(model._name).write(cr, 1, impex_ids, {'state': 'exception'})
            return res
        return wrapper
    return decorator


class IrModelImpex(models.AbstractModel):
    _name = 'ir.model.impex'
    _description = 'Import/Export'
    _rec_name = 'create_date'
    _order = 'create_date desc'

    def __init__(self, pool, cr):
        super(IrModelImpex, self).__init__(pool, cr)
        setattr(Registry, 'load', state_cleaner(pool[self._name])(getattr(Registry, 'load')))

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
    state = fields.Selection(STATES, "State", readonly=True, required=True, default='running')

    @api.multi
    def write_with_new_cursor(self, vals):
        with cursor(self._cr) as new_cr:
            return self.with_env(self.env(cr=new_cr)).write(vals)

    @api.multi
    def process(self):
        self._cr.commit()
        for record in self:
            thread = Thread(target=self.pool[self._name]._process, args=(self._cr, self._uid, record.id, self._context))
            thread.start()
        return True

    def _process(self, cr, uid, impex_id, context=None):
        with api.Environment.manage():
            context = context and context.copy() or {}
            context['logger'] = SmileDBLogger(cr.dbname, self._name, impex_id, uid)
            self.write_with_new_cursor(cr, uid, impex_id, {'state': 'running', 'from_date': fields.Datetime.now()}, context)
            try:
                self._execute(cr, uid, impex_id, context)
                self.write_with_new_cursor(cr, uid, impex_id, {'state': 'done', 'to_date': fields.Datetime.now()}, context)
                if self.browse(cr, uid, impex_id, context).test_mode:
                    cr.rollback()
            except Exception, e:
                context['logger'].error(repr(e))
                self.write_with_new_cursor(cr, uid, impex_id, {'state': 'exception', 'to_date': fields.Datetime.now()}, context)

    @api.one
    @with_new_cursor
    def _execute(self):
        raise NotImplementedError
