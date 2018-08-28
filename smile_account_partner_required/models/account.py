# -*- encoding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2015 Smile (<http://www.smile.fr>). All Rights Reserved
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

from openerp import models, fields, api, exceptions
from openerp.tools.translate import _


class AccountAccount(models.Model):
    _inherit = 'account.account'

    @api.model
    def _get_policies(self):
        """This is the method to be inherited for adding policies"""
        return [('optional', _('Optional')),
                ('always', _('Always')),
                ('never', _('Never'))]

    partner_policy = fields.Selection(_get_policies, string='Policy for partner field', required=True, default='optional',
                                      help="Set the policy for the partner field : if you select "
                                           "'Optional', the accountant is free to put a partner "
                                           "on an account move line with this account ; "
                                           "if you select 'Always', the accountant will get an error "
                                           "message if there is no partner ; if you select 'Never', "
                                           "the accountant will get an error message if a partner "
                                           "is present.")


class AccountMoveLine(models.Model):
    _inherit = "account.move.line"

    @api.one
    @api.constrains('account_id', 'partner_id', 'debit', 'credit')
    def _check_account_partner_required(self):
        if self.account_id.partner_policy == 'always' and not self.partner_id:
            raise exceptions.Warning(_('Error!'), _("Partner policy is set to \'Always\' with account %s \'%s\' but the partner is missing "
                                                    "in the account move line with label \'%s\'.") % (self.account_id.code,
                                                                                                      self.account_id.name,
                                                                                                      self.name))
        elif self.account_id.partner_policy == 'never' and self.partner_id:
            raise exceptions.Warning(_('Error!'), _("Partner policy is set to 'Never' with account %s '%s' \nbut the account move line "
                                                    "with label '%s' has a partner '%s.") % (self.account_id.code,
                                                                                             self.account_id.name,
                                                                                             self.name,
                                                                                             self.partner_id.name))
