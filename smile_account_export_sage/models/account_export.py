# -*- coding: utf-8 -*-

from odoo import fields, models


class AccountExport(models.Model):
    _inherit = 'account.export'

    def _get_sage_filename(self):
        now = fields.Datetime.from_string(fields.Datetime.now())
        year, week = now.isocalendar()[:2]
        return "S{}-{} {}.txt".format(week, year, self.company_id.display_name)

    def _get_sage_format_params(self):
        return {'delimiter': '\t'}

    def _get_sage_add_header(self):
        return False

    def _get_sage_mapping(self):
        return [
            (u'Code journal', 'aml.journal_id.code'),
            (u'Date d\'émission de facture',
             'format_date(aml.move_id.date, \'%d/%m/%Y\')'),
            (u'Libellé de la facture',
             '\'FACT.\' + '
             '(aml.move_id.partner_id.ref or aml.move_id.partner_id.name)'),
            (u'Imputation comptable', 'aml.account_id.code'),
            (u'Code tiers',
             'aml.move_id.partner_id.ref or aml.move_id.partner_id.name'),
            (u'Numéro de pièce', 'aml.move_id.name'),
            (u'Numéro de facture', 'aml.move_id.name'),
            (u'Date d\'échéance',
             'aml.date_maturity and '
             'format_date(aml.date_maturity, \'%d/%m/%Y\') or \'\''),
            (u'Débit', 'format_amount(aml.debit)'),
            (u'Crédit', 'format_amount(aml.credit)'),
        ]
