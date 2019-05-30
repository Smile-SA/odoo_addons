# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import models, api, _, fields
from odoo.exceptions import UserError


class EventRefund(models.TransientModel):

    _name = "event.refund"
    _description = 'Event refund'

    event_id = fields.Many2one("event.event")

    @api.multi
    def button_cancel_with_refund(self):
        """
         Cancel event
        """
        self.ensure_one()
        return self.event_id.button_cancel()

    @api.multi
    def button_cancel_without_refund(self):
        """
        Cancel event and  Refund attendees
        """
        self.ensure_one()
        # Cancel registration
        if self.event_id.registration_ids.filtered(
                lambda l: l.state == 'done'):
            raise UserError(
                _("There are already attendees who attended this event. "
                  "Please reset it to draft if you "
                  "want to cancel this event."))
        for registration_id in self.event_id.registration_ids.filtered(
                lambda l: l.state != 'done'):
            registration_id._process_event_refund()

        # Cancel event
        self.event_id.state = 'cancel'
        return True
