# -*- encoding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2016 Smile (<http://www.smile.fr>). All Rights Reserved
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

from openerp import models, api


class EventEvent(models.Model):
    _inherit = 'event.event'

    @api.model
    def create(self, vals):
        event = super(EventEvent, self).create(vals)
        calendar_event_vals = {'name': event.name,
                               'start_datetime': event.date_begin,
                               'stop_datetime': event.date_end,
                               'start': event.date_begin,
                               'stop': event.date_end,
                               'allday': False,
                               'location': event.address_id and event.address_id.name,
                               'class': 'public',
                               'show_as': 'free',
                               'partner_ids': [(6, 0, [])],
                               'event_event_id': event.id, }
        self.env['calendar.event'].create(calendar_event_vals)
        return event

    @api.multi
    def write(self, vals):
        calendar_event_vals = {}
        onchange_date = []
        if vals.get('name'):
            calendar_event_vals['name'] = vals.get('name')
        if vals.get('date_begin'):
            calendar_event_vals['start_datetime'] = vals.get('date_begin')
            onchange_date.append('start')
        if vals.get('date_end'):
            calendar_event_vals['stop_datetime'] = vals.get('date_end')
            onchange_date.append('stop')
        if vals.get('address_id'):
            calendar_event_vals['location'] = self.env['res.partner'].sudo().browse(vals.get('address_id')).name
        res = super(EventEvent, self).write(vals)
        if calendar_event_vals and not self._context.get('from_calendar'):
            calendar_event_ids = self.env['calendar.event'].search([('event_event_id', 'in', self.ids)])
            calendar_event_ids.write(calendar_event_vals)
            for calendar_event_id in calendar_event_ids:
                allday = calendar_event_id.allday
                for fromtype in onchange_date:
                    start = calendar_event_vals.get('start_datetime', False)
                    end = calendar_event_vals.get('stop_datetime', False)
                    calendar_event_id.with_context(from_event=True).onchange_dates(fromtype, start, end, allday,
                                                                                   allday)
        return res
