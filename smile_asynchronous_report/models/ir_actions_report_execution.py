# -*- coding: utf-8 -*-
# (C) 2018 Smile (<http://www.smile.fr>)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

import base64
import logging
import time

from odoo import api, fields, models, registry, _
from odoo.tools.misc import unquote
from odoo.tools.safe_eval import safe_eval

_logger = logging.getLogger(__name__)


class IrActionsReportExecution(models.TransientModel):
    _name = 'ir.actions.report.execution'
    _description = 'Asynchronous printing'
    _inherit = 'mail.thread'
    _rec_name = 'create_date'
    _order = 'create_date desc'

    create_uid = fields.Many2one('res.users', 'Created by', readonly=True)
    create_date = fields.Datetime('Created on', readonly=True)
    report_id = fields.Many2one(
        'ir.actions.report', 'Report', required=True, ondelete='cascade',
        readonly=True)
    arguments = fields.Text(readonly=True)
    context = fields.Text(readonly=True)
    state = fields.Selection([
        ('draft', 'Draft'),
        ('done', 'Done'),
    ], required=True, readonly=True, copy=False, default='draft')
    time = fields.Float(readonly=True)
    attachment_id = fields.Many2one(
        'ir.attachment', 'Attachment', compute='_get_attachment')
    user_ids = fields.Many2many('res.users', string='Followers')

    @api.one
    @api.depends('state')
    def _get_attachment(self):
        self.attachment_id = self.env['ir.attachment'].search([
            ('res_model', '=', self._name),
            ('res_id', '=', self.id),
        ], limit=1)

    @api.model
    def auto_print_report(self):
        for execution in self.search([('state', '=', 'draft')]):
            execution.sudo(execution.create_uid).print_report()
        return True

    @api.multi
    def print_report(self):
        self.ensure_one()
        report = self.report_id
        args = safe_eval(self.arguments)
        ctx = self._eval_context()
        ctx['force_render_qweb_pdf'] = True
        attachments = None
        t0 = time.time()
        try:
            report_name = self._format_report_name(report.name)
            content, ext = report.with_context(ctx).render_qweb_pdf(*args)
            attachments = [(report_name, content)]
            self.sudo()._add_attachment(content)
            msg = _('%s report available') % report_name
        except Exception as e:
            _logger.error(e)
            msg = _('%s printing failed') % report_name
        finally:
            # INFO: use a new cursor to:
            # 1. avoid concurrent updates
            # 2. have access to the whole list of followers
            # if some followers were added during printing
            with registry(self._cr.dbname).cursor() as new_cr:
                self = self.with_env(self.env(cr=new_cr))
                self.write({
                    'time': time.time() - t0,
                    'state': 'done',
                })
                self.sudo()._send_notification(msg, attachments)
            return True

    @api.multi
    def _eval_context(self):
        self.ensure_one()
        eval_dict = {
            'active_id': unquote("active_id"),
            'active_ids': unquote("active_ids"),
            'active_model': unquote("active_model"),
            'uid': self.create_uid.id,
            'context': self._context,
        }
        return safe_eval(self.context, eval_dict)

    @api.one
    def _add_attachment(self, content):
        report = self.report_id
        res_ids = safe_eval(self.arguments)[0]
        report_name = report.name
        if report.attachment and res_ids and len(res_ids) == 1:
            record = self.env[report.model].browse(res_ids[0])
            report_name = safe_eval(
                report.attachment,
                {'object': record, 'time': time}) or report_name
        report_name = self._format_report_name(report_name)
        self.env['ir.attachment'].create({
            'name': report_name,
            'datas': base64.encodestring(content),
            'datas_fname': report_name,
            'res_model': self._name,
            'res_id': self.id,
        })

    @api.model
    def _format_report_name(self, report_name):
        lang = self._context.get('lang') or self.env.user.lang
        report_name = self.env['ir.translation']._get_source(
            None, 'model', lang, report_name)
        return '{}.pdf'.format(report_name)

    @api.one
    def _send_notification(self, msg, attachments=None):
        kwargs = self._get_message_post_arguments(msg, attachments)
        for user in self.create_uid | self.user_ids:
            self._get_channel(user).message_post(**kwargs)

    @api.model
    def _get_system_user(self):
        """ Return system user used to send notification.
        """
        return self.env.ref('smile_asynchronous_report.user_system')

    @api.multi
    def _get_message_post_arguments(self, msg, attachments):
        system_user = self._get_system_user()
        return {
            'author_id': system_user.partner_id.id,
            'email_from': False,  # To avoid to get author from email data
            'body': msg,
            'message_type': 'comment',
            'subtype': 'mail.mt_comment',
            'content_subtype': 'plaintext',
            'attachments': attachments,
        }

    @api.multi
    def _get_channel(self, user):
        self.ensure_one()
        domain = [
            ('channel_type', '=', 'chat'),
            ('public', '=', 'private'),
        ]
        system_user = self._get_system_user()
        partners = (user | system_user).mapped('partner_id')
        for partner in partners:
            domain.append(('channel_partner_ids', 'in', partner.id))
        channel = self.env['mail.channel'].search(domain, limit=1)
        if not channel:
            channel = channel.create({
                'name': ', '.join(partners.mapped('name')),
                'channel_type': 'chat',
                'public': 'private',
                'channel_partner_ids': [(6, 0, partners.ids)],
            })
        return channel
