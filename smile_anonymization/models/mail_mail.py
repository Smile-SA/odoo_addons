# -*- coding: utf-8 -*-
# (C) 2019 Smile (<http://www.smile.fr>)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from openerp.osv import orm, fields


class MailMail(orm.Model):
    _inherit = 'mail.mail'

    _columns = {
        'body_html': fields.char(data_mask="'mail_' || id::text"),
        'email_to': fields.char(data_mask="NULL"),
        'email_cc': fields.char(data_mask="NULL"),
    }
