# -*- coding: utf-8 -*-
# (C) 2022 Smile (<https://www.smile.eu>)
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl).

from odoo import models, _
from odoo.exceptions import RedirectWarning, UserError, ValidationError


class Partner(models.Model):
    _inherit = "res.partner"

    def write(self, vals):
        """Override write to add context from_create_profile in condition."""
        if vals.get('active') is False and not self._context.get('from_create_profile'):
            # DLE: It should not be necessary to modify this to make work the ORM. The problem was just the recompute
            # of partner.user_ids when you create a new user for this partner, see test test_70_archive_internal_partners
            # You modified it in a previous commit, see original commit of this:
            # https://github.com/odoo/odoo/commit/9d7226371730e73c296bcc68eb1f856f82b0b4ed
            #
            # RCO: when creating a user for partner, the user is automatically added in partner.user_ids.
            # This is wrong if the user is not active, as partner.user_ids only returns active users.
            # Hence this temporary hack until the ORM updates inverse fields correctly.
            self.invalidate_recordset(['user_ids'])
            users = self.env['res.users'].sudo().search([('partner_id', 'in', self.ids)])
            if users:
                if self.env['res.users'].sudo(False).check_access_rights('write', raise_exception=False):
                    error_msg = _('You cannot archive contacts linked to an active user.\n'
                                  'You first need to archive their associated user.\n\n'
                                  'Linked active users : %(names)s', names=", ".join([u.display_name for u in users]))
                    action_error = users._action_show()
                    raise RedirectWarning(error_msg, action_error, _('Go to users'))
                else:
                    raise ValidationError(_('You cannot archive contacts linked to an active user.\n'
                                            'Ask an administrator to archive their associated user first.\n\n'
                                            'Linked active users :\n%(names)s', names=", ".join([u.display_name for u in users])))
        # res.partner must only allow to set the company_id of a partner if it
        # is the same as the company of all users that inherit from this partner
        # (this is to allow the code from res_users to write to the partner!) or
        # if setting the company_id to False (this is compatible with any user
        # company)
        if vals.get('website'):
            vals['website'] = self._clean_website(vals['website'])
        if vals.get('parent_id'):
            vals['company_name'] = False
        if 'company_id' in vals:
            company_id = vals['company_id']
            for partner in self:
                if company_id and partner.user_ids:
                    company = self.env['res.company'].browse(company_id)
                    companies = set(user.company_id for user in partner.user_ids)
                    if len(companies) > 1 or company not in companies:
                        raise UserError(
                            ("The selected company is not compatible with the companies of the related user(s)"))
                if partner.child_ids:
                    partner.child_ids.write({'company_id': company_id})
        result = True
        # To write in SUPERUSER on field is_company and avoid access rights problems.
        if 'is_company' in vals and self.user_has_groups('base.group_partner_manager') and not self.env.su:
            result = super(Partner, self.sudo()).write({'is_company': vals.get('is_company')})
            del vals['is_company']
        if not self._context.get('from_create_profile'):
            result = result and super(Partner, self).write(vals)
        else:
            result = result
        for partner in self:
            if any(u._is_internal() for u in partner.user_ids if u != self.env.user):
                self.env['res.users'].check_access_rights('write')
            partner._fields_sync(vals)
        return result
