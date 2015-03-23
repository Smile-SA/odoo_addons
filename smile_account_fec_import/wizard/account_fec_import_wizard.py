# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2014 Smile (<http://www.smile.fr>).
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

import csv
import cStringIO

from openerp import api, fields, models, _
from openerp.exceptions import Warning


class AccountFecImportWizard(models.TransientModel):
    _name = 'account.fr.fec.import'
    _description = 'FEC import wizard'
    _rec_name = 'fec_file'

    fec_file = fields.Binary(required=True)
    account_journal_ids = fields.Many2many('account.journal', string='Account Journals',
                                           help="Let it empty if you want to import all account moves")
    import_reconciliation = fields.Boolean(default=True)
    delimiter = fields.Char(required=True, default='|')

    @api.multi
    def import_file(self):
        self.ensure_one()
        data = []
        filecontent = self.fec_file.decode('base64')
        csvfile = cStringIO.StringIO(filecontent)
        for index, row in enumerate(csv.reader(csvfile, delimiter=str(self.delimiter))):
            if not index:
                header = row
            else:
                data.append(dict(zip(header, row)))
        self._filter_data(data)
        self._import_data(data)

    @api.multi
    def _filter_data(self, data):
        self.ensure_one()
        if self.import_reconciliation:
            all_data = data[:]
        journal_codes = self.account_journal_ids.mapped('code')
        if journal_codes:
            for index, row in enumerate(data):
                if row['JournalCode'] not in journal_codes:
                    del data[index]
        if self.import_reconciliation:
            reconcile_codes = map(lambda row: row['EcritureLet'], data)
            reconcile_refs_by_code = {}
            for row in filter(lambda row: row['EcritureLet'] and row['EcritureLet'] in reconcile_codes, all_data):
                reconcile_refs_by_code.setdefault(row['EcritureLet'], set()).add(row['PieceRef'])
            for row in data:
                row['ReconciliationRef'] = reconcile_refs_by_code[row['EcritureLet']]

    @api.model
    def _import_data(self, data):
        move_obj = self.env['account.move']
        line_obj = self.env['account.move.line']
        move = None
        for row in data:
            if move and row['EcritureNum'] != move.name:
                move.post()
                move = None
            move_vals = {}
            line_vals = {}
            for col in row:
                value = row[col]
                if not move:
                    if col == 'JournalCode':
                        move_vals['journal_id'] = self._get_record_id(value, 'account.journal')
                    elif col == 'EcritureNum':
                        move_vals['name'] = value
                    elif col == 'EcritureDate':
                        move_vals['date'] = self._get_date(value)
                        move_vals['period_id'] = self._get_period_id(move_vals['date'])
                    elif col == 'PieceRef':
                        move_vals['ref'] = value
                if col == 'CompteNum':
                    line_vals['account_id'] = self._get_record_id(value, 'account.account')
                elif col == 'CompAuxNum' and value:
                    line_vals['partner_id'] = self._get_record_id(value, 'res.partner', 'id')
                elif col == 'EcritureLib':
                    line_vals['name'] = value
                elif col == 'Debit':
                    line_vals['debit'] = self._get_amount(value)
                elif col == 'Credit':
                    line_vals['credit'] = self._get_amount(value)
                elif col == 'Montant':
                    line_vals[row['Sens'] in ('D', '+1') and 'debit' or 'credit'] = self._get_amount(value)
                if col in ('Montantdevise', 'Idevise') and row['Idevise'] and \
                        row['Idevise'] != self.env.user.company_id.currency_id.name:
                    if col == 'Montantdevise':
                        line_vals['amount_currency'] = self._get_amount(value, sign=True)
                    elif col == 'Idevise':
                        line_vals['currency_id'] = self._get_record_id(value, 'res.currency', 'name')
            if not move:
                move = move_obj.create(move_vals)
            line_vals['move_id'] = move.id
            line = line_obj.create(line_vals)
            self._reconcile(row['ReconciliationRef'], line.period_id.fiscalyear_id.id, row['EcritureLet'])
        if move:  # For last row
            move.post()

    @api.model
    def _reconcile(self, move_refs, fiscalyear_id, name):
        if move_refs and len(move_refs) > 1:
            line_obj = self.env['account.move.line']
            lines_to_reconcile = line_obj.search([('move_id.ref', 'in', list(move_refs)),
                                                  ('account_id.reconcile', '=', True),
                                                  ('period_id.fiscalyear_id', '=', fiscalyear_id)])
            if len(move_refs) == len(lines_to_reconcile):
                reconcile_id = line_obj.reconcile_partial(lines_to_reconcile.ids)
                self.env['account.move.reconcile'].browse(reconcile_id).name = name

    _fec_cache = {}

    @api.model
    def _get_cache(self, model, field='code'):
        company_id = self.env.user.company_id.id
        if company_id not in self._fec_cache or model not in self._fec_cache[company_id]:
            values = dict((rec[field], rec['id']) for rec in self.env[model].search_read([], [field]))
            self._fec_cache.setdefault(company_id, {})[model] = values
        return self._fec_cache[company_id][model]

    @api.model
    def _get_record_id(self, code, model, field='code'):
        records = self._get_cache(model, field)
        if code not in records:
            raise Warning(_("The %s %%s doesn't exist" % self.env[model]._description) % code)
        return records[code]

    @api.model
    def _get_amount(self, value, sign=False):
        amount = eval(value.replace(',', '.') or '0.0')
        return amount if sign else abs(amount)

    @api.model
    def _get_date(self, date):
        return '%s-%s-%s' % (date[:4], date[4:6], date[6:])

    @api.model
    def _get_period_id(self, date):
        period = self.env['account.period'].find(date)
        if not period:
            raise Warning(_("No period for %s") % date)
        return period.id
