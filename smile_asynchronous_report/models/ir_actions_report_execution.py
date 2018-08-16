# -*- coding: utf-8 -*-
# (C) 2018 Smile (<http://www.smile.fr>)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

import base64
import logging
import time

from odoo import api, fields, models, registry, SUPERUSER_ID, _
from odoo.tools.misc import unquote
from odoo.tools.safe_eval import safe_eval

_logger = logging.getLogger(__name__)


class IrActionsReportExecution(models.TransientModel):
    _name = 'ir.actions.report.execution'
    _description = 'Asynchronous printing'
    _inherit = 'mail.thread'
    _rec_name = 'create_date'
    _order = 'create_date desc'

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
            execution.print_report()
        return True

    @api.multi
    def print_report(self):
        self.ensure_one()
        report = self.report_id
        args = safe_eval(self.arguments)
        ctx = self._eval_context()
        ctx['force_render_qweb_pdf'] = True
        t0 = time.time()
        try:
            content, ext = report.with_context(ctx).render_qweb_pdf(*args)
            self._add_attachment(content)
            msg = _('%s report available') % report.name
        except Exception as e:
            _logger.error(e)
            msg = _('%s printing failed') % report.name
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
                self._send_notification(msg)
            return True

    @api.multi
    def _eval_context(self):
        self.ensure_one()
        eval_dict = {
            'active_id': unquote("active_id"),
            'active_ids': unquote("active_ids"),
            'active_model': unquote("active_model"),
            'uid': self._uid,
            'context': self._context,
        }
        return safe_eval(self.context, eval_dict)

    @api.multi
    def _add_attachment(self, content):
        self.ensure_one()
        report = self.report_id
        res_ids = safe_eval(self.arguments)[0]
        name = report.name
        if report.attachment and res_ids and len(res_ids) == 1:
            record = self.env[report.model].browse(res_ids[0])
            name = safe_eval(report.attachment,
                             {'object': record, 'time': time}) or name
        self.env['ir.attachment'].create({
            'name': name,
            'datas': base64.encodestring(content),
            'datas_fname': name,
            'res_model': self._name,
            'res_id': self.id,
        })

    @api.one
    def _send_notification(self, msg):
        self.ensure_one()
        author = self.env['res.users'].browse(SUPERUSER_ID).partner_id
        kwargs = {
            'author_id': author.id,
            'email_from': False,  # To avoid to get author from email data
            'body': msg,
            'message_type': 'comment',
            'subtype': 'mail.mt_comment',
            'content_subtype': 'plaintext',
        }
        if self.attachment_id:
            kwargs['attachment_ids'] = self.attachment_id.ids
        self._get_channel().message_post(**kwargs)

    @api.multi
    def _get_channel(self):
        self.ensure_one()
        partners = self.env.user.partner_id | \
            self.env['res.users'].browse(SUPERUSER_ID).partner_id
        channel = self.env['mail.channel'].search([
            ('channel_type', '=', 'chat'),
            ('public', '=', 'private'),
            ('channel_partner_ids', 'in', partners.ids),
        ], limit=1)
        if not channel:
            channel = channel.create({
                'name': ', '.join(partners.mapped('name')),
                'channel_type': 'chat',
                'public': 'private',
                'channel_partner_ids': [(6, 0, partners.ids)],
            })
        return channel
