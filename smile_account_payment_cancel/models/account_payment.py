# -*- coding: utf-8 -*-

from odoo import api, models


class AccountPayment(models.Model):
    _inherit = 'account.payment'

    @api.multi
    def cancel(self):
        if self._context.get('reversal_date'):
            self.mapped('move_line_ids.move_id').reverse_moves(
                date=self._context['reversal_date'])
            return self.write({'state': 'cancelled'})
        posted_payments = self.filtered(
            lambda payment: payment.state in ('posted', 'reconciled'))
        if posted_payments:
            return {
                'type': 'ir.actions.act_window',
                'res_model': 'account.payment.reversal',
                'view_mode': 'form',
                'view_id': False,
                'context': {'payment_ids': self.ids},
                'target': 'new',
            }
        return super(AccountPayment, self).cancel()
