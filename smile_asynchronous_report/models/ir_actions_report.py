# -*- coding: utf-8 -*-

import base64
import logging
from threading import Thread
import time

from odoo import api, fields, models, SUPERUSER_ID, _
from odoo.exceptions import UserError
from odoo.sql_db import db_connect
from odoo.tools.misc import unquote
from odoo.tools.safe_eval import safe_eval

_logger = logging.getLogger(__name__)


class IrActionsReport(models.Model):
    _inherit = 'ir.actions.report'

    execution_mode = fields.Selection([
        ('sync', 'Synchronous'),
        ('async', 'Asynchronous'),
    ], required=True, default='sync')

    @api.multi
    def render_qweb_pdf(self, res_ids=None, data=None):
        if not self._context.get('force_render_qweb_pdf'):
            content = self.render_in_asynchronous_mode(res_ids, data)
            if content:
                return content, 'pdf'
        return super(IrActionsReport, self).render_qweb_pdf(res_ids, data)

    @api.multi
    def render_in_asynchronous_mode(self, res_ids, data):
        self.ensure_one()
        if self.execution_mode == 'async':
            thread = Thread(
                target=IrActionsReport._check_execution_in_new_thread,
                args=(self, res_ids, data))
            thread.start()
            raise UserError(_('Printing in progress. '
                              'You will be notified as soon as done.'))

    @api.one
    def _check_execution_in_new_thread(self, res_ids, data):
        with api.Environment.manage():
            with db_connect(self._cr.dbname).cursor() as new_cr:
                self = self.with_env(self.env(cr=new_cr))
                self._check_execution(res_ids, data)

    @api.one
    def _check_execution(self, res_ids, data):
        arguments = repr((res_ids, data))
        context = repr(self._context)
        execution = self.env['ir.actions.report.execution'].search([
            ('report_id', '=', self.id),
            ('arguments', '=', arguments),
            ('context', '=', context),
        ], limit=1)
        if execution:
            if execution.state == 'done':
                msg = _('%s report available') % execution.report_id.name
                execution._send_notification(msg)
            else:
                execution.user_ids |= self.env.user
        else:
            execution.create({
                'report_id': self.id,
                'arguments': arguments,
                'context': context,
            })


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
    def create(self, vals):
        record = super(IrActionsReportExecution, self).create(vals)
        record.print_report()
        return record

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
