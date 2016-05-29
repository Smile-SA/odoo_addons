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

from openerp import models, fields, api, _
from openerp.exceptions import Warning


class CalendarEvent(models.Model):
    _inherit = 'calendar.event'

    event_event_id = fields.Many2one('event.event', string='Event', ondelete='cascade', readonly=True)

    @api.multi
    def write(self, vals):
        event_ids = self.mapped('event_event_id')
        if event_ids and 'event_event_id' in vals and not vals.get('event_event_id'):
            raise Warning(_('You cannot change event value if is already assign'))
        event_vals = {}
        if 'start_datetime' in vals:
            event_vals['date_begin'] = vals.get('start_datetime')
        if 'stop_datetime' in vals:
            event_vals['date_end'] = vals.get('stop_datetime')
        if event_ids and not all(event_vals):
            raise Warning(_('You cannot remove start or stop date if one of the current record have and event'))
        res = super(CalendarEvent, self).write(vals)
        if event_ids and event_vals and not self._context.get('from_event'):
            event_ids.with_context(from_calendar=True).write(event_vals)
        return res
