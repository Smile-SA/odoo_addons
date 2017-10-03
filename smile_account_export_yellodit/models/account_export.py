# -*- coding: utf-8 -*-

from odoo import fields, models


class AccountExport(models.Model):
    _inherit = 'account.export'

    def _get_yellodit_filename(self):
        now = fields.Datetime.now().replace(' ', '_') \
            .replace('-', '').replace(':', '')
        return "Export_yellodit_{}.csv".format(now)

    def _get_yellodit_format_params(self):
        return {'delimiter': ";"}

    def _get_yellodit_mapping(self):
        return [
            (u'Code journal', 'aml.journal_id.code'),
            (u'Date écriture', 'aml.move_id.date'),
            (u'Numéro de pièce', 'aml.move_id.name'),
            (u'Code compte', 'aml.account_id.code'),
            (u'Libellé écriture', 'aml.name'),
            (u'Débit origine', 'format_amount(aml.debit, ",")'),
            (u'Crédit origine', 'format_amount(aml.credit, ",")'),
            (u'Axe 1 analytique', ''),
            (u'Axe 2 analytique', ''),
            (u'Axe 3 analytique', ''),
        ]
