# -*- coding: utf-8 -*-

import base64
import unicodecsv as csv
import io

from odoo import api, fields, models, _
from odoo.exceptions import UserError
from odoo.tools.safe_eval import safe_eval

from ..tools import format_amount, format_date


class AccountExport(models.Model):
    _name = 'account.export'
    _description = 'Account Export'
    _inherits = {'account.export.template': 'export_tmpl_id'}
    _order = 'generation_date desc'

    export_tmpl_id = fields.Many2one(
        'account.export.template', 'Export template', required=True,
        readonly=True, states={'draft': [('readonly', False)]})
    state = fields.Selection([
        ('draft', 'Draft'),
        ('done', 'Exported'),
        ('test', 'Tested'),
        ('cancel', 'Cancelled'),
    ], required=True, default='draft', readonly=True)
    generation_date = fields.Datetime(copy=False, readonly=True)
    start_date = fields.Date(
        copy=False, readonly=True, states={'draft': [('readonly', False)]})
    stop_date = fields.Date(
        required=True, default=lambda self: fields.Date.today(),
        copy=False, readonly=True, states={'draft': [('readonly', False)]})
    account_move_line_ids = fields.Many2many(
        'account.move.line', string='Journal Items', readonly=True,
        compute='_get_account_move_lines', inverse='_set_account_move_lines')
    record_ids = fields.Text(
        'Record Ids (technical field)', required=True, default='[]',
        readonly=True, copy=False)
    account_move_lines_count = fields.Integer(
        'Number of journal items', compute='_get_account_move_lines')
    account_moves_count = fields.Integer(
        'Number of journal entries', compute='_get_account_move_lines')
    debit = fields.Integer('Debit', compute='_get_account_move_lines')
    credit = fields.Integer('Credit', compute='_get_account_move_lines')

    @api.constrains('start_date', 'stop_date')
    def check_dates(self):
        if self.start_date > self.stop_date:
            raise UserError(_("Start date cannot be later than stop date"))

    @api.one
    @api.depends('record_ids')
    def _get_account_move_lines(self):
        ids = safe_eval(self._format_record_ids(self.record_ids, reverse=True))
        self.account_move_line_ids = self.env['account.move.line'].browse(ids)
        self.account_move_lines_count = len(self.account_move_line_ids)
        if self.account_move_lines_count:
            self.account_moves_count = len(
                self.account_move_line_ids.mapped('move_id'))
            self.debit = sum(self.account_move_line_ids.mapped('debit'))
            self.credit = sum(self.account_move_line_ids.mapped('credit'))
        else:
            self.account_moves_count = self.debit = self.credit = 0

    @api.one
    def _set_account_move_lines(self):
        ids = repr(self.account_move_line_ids.ids).replace(' ', '')
        self.record_ids = self._format_record_ids(ids)

    @api.model
    def _format_record_ids(self, record_ids, reverse=False):
        for i, j in [('[', '[,'), (']', ',]')]:
            if reverse:
                i, j = j, i
            record_ids = record_ids.replace(i, j)
        return record_ids

    @api.one
    def name_get(self):
        name = self.name
        if self.generation_date:
            name += ' %s' % self.generation_date
        return self.id, name

    @api.multi
    def unlink(self):
        if 'done' in self.mapped('state'):
            raise UserError(_("You can't delete done exports!"))
        return super(AccountExport, self).unlink()

    @api.multi
    def button_show_lines(self):
        """Display move lines that were exported."""
        self.ensure_one()
        lines = self.account_move_line_ids
        return {
            'type': 'ir.actions.act_window',
            'res_model': lines._name,
            'view_mode': 'tree,form',
            'view_id': False,
            'domain': [('id', 'in', lines.ids)],
            'target': 'current',
        }

    @api.multi
    def save_attachment(self, datas):
        """Attach the exported file to the export."""
        self.ensure_one()
        filename = getattr(self, '_get_%s_filename' % self.provider)()
        return self.env['ir.attachment'].create({
            'name': filename,
            'datas_fname': filename,
            'datas': base64.encodestring(datas),
            'res_model': self._name,
            'res_id': self.id,
            'company_id': self.company_id.id
        })

    @api.multi
    def get_account_move_lines_domain(self):
        self.ensure_one()
        domain = [
            ('company_id', '=', self.company_id.id),
            ('date', '<=', self.stop_date),
        ]
        if self.start_date:
            domain.append(('date', '>=', self.start_date))
        if not self.force_export:
            domain.append(('exported', '=', False))
        if self.journal_ids:
            domain.append(('journal_id', 'in', self.journal_ids.ids))
        if self.account_ids:
            domain.append(('account_id', 'in', self.account_ids.ids))
        return domain

    @api.multi
    @api.returns('account.move.line', lambda records: records.ids)
    def filter_account_move_lines(self):
        domain = self.get_account_move_lines_domain()
        return self.env['account.move.line'].search(domain)

    @api.multi
    def cancel_export(self):
        """Reset export state of move lines and cancel exports."""
        exports = self.filtered(lambda export: export.state == 'done')
        return exports.write({'state': 'cancel'})

    @api.multi
    def mark_as_tested(self):
        self.write({
            'state': 'test',
            'generation_date': fields.Datetime.now(),
        })

    @api.multi
    def mark_as_exported(self, account_move_line_ids):
        self.write({
            'state': 'done',
            'account_move_line_ids': [(6, 0, account_move_line_ids)],
            'generation_date': fields.Datetime.now(),
        })

    @api.model
    def _get_eval_context(self):
        return {'format_amount': format_amount, 'format_date': format_date}

    @api.multi
    def run_export(self):
        """Export move lines according to filters and
        attach generated file to the export."""
        self.ensure_one()
        if self.state == 'cancel':
            raise UserError(_('You cannot run a cancelled export!'))
        account_move_lines = self.filter_account_move_lines()
        if not account_move_lines:
            raise UserError(_("There is no move lines to export."))
        with io.BytesIO() as output:
            mapping = getattr(self, '_get_%s_mapping' % self.provider)()
            fieldnames, dummy = zip(*mapping)
            mapping = dict(mapping)
            format_params_method = '_get_%s_format_params' % self.provider
            format_params = hasattr(self, format_params_method) and \
                getattr(self, format_params_method)() or {}
            writer = csv.DictWriter(output, fieldnames=fieldnames,
                                    **format_params)
            add_header_method = '_get_%s_add_header' % self.provider
            add_header = getattr(self, add_header_method)() \
                if hasattr(self, add_header_method) else True
            if add_header:
                writer.writeheader()
            eval_context = self._get_eval_context()
            for aml in account_move_lines:
                line_infos = {}
                eval_context['aml'] = aml
                for header, expr in mapping.iteritems():
                    if expr:
                        line_infos[header] = safe_eval(expr, eval_context)
                    else:
                        line_infos[header] = ''
                writer.writerow(line_infos)
            attachment = self.save_attachment(output.getvalue())
        self.post_message(attachment.ids)
        if self._context.get('test_mode'):
            self.mark_as_tested()
        else:
            self.mark_as_exported(account_move_lines.ids)
        return True

    @api.multi
    def post_message(self, attachment_ids=None):
        self.ensure_one()
        timestamp = fields.Datetime.from_string(fields.Datetime.now())
        now = fields.Datetime.context_timestamp(
            self.export_tmpl_id.create_uid, timestamp)
        if self._context.get('test_mode'):
            msg = _('Test account export on %s')
        else:
            msg = _('New account export on %s')
        self.export_tmpl_id.message_post(msg % now,
                                         attachment_ids=attachment_ids)
        return True
