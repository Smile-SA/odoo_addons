# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2015 UGC
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

from datetime import datetime
from dateutil.relativedelta import relativedelta
import time

from openerp import models, fields, api


class IrFiltersCategory(models.Model):
    _name = 'ir.filters.category'
    _description = 'Filters Category'

    name = fields.Char(required=True, translate=True)
    sequence = fields.Integer()
    fold = fields.Boolean('Folded by Default')


class IrFilters(models.Model):
    _inherit = 'ir.filters'

    @api.multi
    def _get_domain_and_context(self):
        self.ensure_one()
        localdict = {
            'time': time,
            'datetime': datetime,
            'relativedelta': relativedelta,
            'uid': self._uid,
            'user': self.env.user,
        }
        context = eval(self.context, localdict)
        localdict['context'] = context
        domain = eval(self.domain, localdict)
        return domain, context

    @api.one
    def _get_count(self):
        domain, context = self._get_domain_and_context()
        self.count = self.env[self.model_id].with_context(
            context).search_count(domain)

    name = fields.Char(translate=True)
    todo_list = fields.Boolean()
    category_id = fields.Many2one('ir.filters.category', 'Todo category')
    color = fields.Integer('Color Index')
    group_ids = fields.Many2many('res.groups', string='Groups')
    count = fields.Integer(compute='_get_count')
    todo_action_id = fields.Many2one(
        'ir.actions.act_window', 'Todo Action', ondelete='set null')

    @api.model
    def _get_action_domain(self, action_id=None):
        return [('todo_list', '=', False)] + \
            super(IrFilters, self)._get_action_domain(action_id)

    @api.model
    def create(self, values):
        if values.get('todo_list') and not values.get('todo_action_id') and \
                values.get('action_id'):
            act_window_obj = self.env['ir.actions.act_window']
            values['todo_action_id'] = act_window_obj.search(
                [('id', '=', values.get('action_id'))]).id or False
        return super(IrFilters, self).create(values)

    @api.multi
    def view_details(self):
        self.ensure_one()
        domain, context = self._get_domain_and_context()
        if self.todo_action_id:
            action = self.todo_action_id.read([])
            if action:
                action = action[0]
                if self.domain:
                    action['domain'] = self.domain
                return action
        view_types = self.env['ir.ui.view'].sudo().search([
            ('model', '=', self.model_id),
            ('inherit_id', '=', False),
            ('type', 'in', ('kanban', 'tree', 'form')),
        ]).mapped('type')
        kwargs = {
            'name': self.name,
            'target': 'current',
            'view_mode': ','.join(set(view_types)),
            'domain': domain,
            'context': context,
        }
        return self.env[self.model_id].with_context(
            context).browse().open_wizard(**kwargs)

    @api.multi
    def _read_group_category_ids(self, domain, **kwargs):
        categories = self.env['ir.filters.category'].search([])
        return categories.name_get(), \
            {categ.id: categ.fold for categ in categories}

    _group_by_full = {
        'category_id': _read_group_category_ids,
    }
