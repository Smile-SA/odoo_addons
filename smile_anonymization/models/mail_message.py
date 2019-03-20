# -*- coding: utf-8 -*-
# (C) 2019 Smile (<http://www.smile.fr>)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from openerp.osv import orm, fields


class MailMessage(orm.Model):
    _inherit = 'mail.message'

    _columns = {
        'subject': fields.char(data_mask="'subject_' || id::text"),
        'body': fields.char(data_mask="'body_' || id::text"),
        'record_name': fields.char(data_mask="model || ',' || res_id::text"),
        'email_from': fields.char(data_mask="NULL"),
        'message_id': fields.char(data_mask="NULL"),
    }
