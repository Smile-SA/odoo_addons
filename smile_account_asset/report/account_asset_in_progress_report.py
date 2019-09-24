# -*- coding: utf-8 -*-

from odoo import api, models


class ReportAccountAssetsInProgress(models.AbstractModel):
    _name = 'report.smile_account_asset.report_account_assets_in_progress'
    _inherit = 'account.asset.report.mixin'

    @api.model
    def _get_records(self, data):
        """
        Retourne les lignes de facture associées à
        * une immobilisation en cours à la date de fin
        * aucune immobilisation mais liée à une catégorie d'immobilisation
            en cours
        """
        domain = self._get_records_to_display_domain(data)
        # Supprime les lignes de facture
        # * liées à aucune immobilisation
        #   et liées à une catégorie autre que celles indiquées
        #     dans l'assistant du rapport
        # * liées à une immobilisation qui n'est
        #   plus en cours à la date de fin
        #   ou liées à une catégorie autre que celles indiquées
        #     dans l'assistant du rapport
        form = data['form']
        category_ids = form['category_ids']
        date_to = form['date_to']
        invoice_lines = self.env['account.invoice.line'].search(domain)
        for invoice_line in invoice_lines[:]:
            if not invoice_line.asset_id and category_ids and \
                    invoice_line.asset_category_id.id not in category_ids:
                invoice_lines -= invoice_line
            elif invoice_line.asset_id and \
                    not invoice_line.asset_id.category_id.asset_in_progress:
                for history in invoice_line.asset_id.asset_history_ids. \
                        sorted('date_to'):
                    if history.date_to.isoformat() > date_to:
                        asset_category = history.asset_category_id
                        if not asset_category.asset_in_progress or \
                                category_ids and \
                                asset_category.id not in category_ids:
                            invoice_lines -= invoice_line
                        break
        return invoice_lines

    @api.model
    def _get_records_to_display_domain(self, data):
        form = data['form']
        date_from = form['date_from']
        date_to = form['date_to']
        domain = [
            ('asset_category_id.asset_in_progress', '=', True),
            '|',
            '&', '&',
            ('invoice_id.date', '!=', False),
            ('invoice_id.date', '>=', date_from),
            ('invoice_id.date', '<=', date_to),
            '&', '&',
            ('invoice_id.date', '=', False),
            ('invoice_id.date_invoice', '>=', date_from),
            ('invoice_id.date_invoice', '<=', date_to),
        ]
        if form['partner_ids']:
            domain += [('invoice_id.partner_id', 'in', form['partner_ids'])]
        if form['account_ids']:
            domain += [('account_id', 'in', form['account_ids'])]
        return domain

    @api.model
    def group_by(self, invoice_lines, currency, date_to):
        """ Group invoice lines by: account.
        Compute invoice line infos for each line.
        """
        group_by = {}
        for invoice_line in invoice_lines:
            invoice_line_infos = self._get_invoice_line_infos(
                invoice_line, currency, date_to)
            if not invoice_line_infos:
                continue
            invoice_line_account = invoice_line_infos['account']
            del invoice_line_infos['account']
            group_by.setdefault(invoice_line_account, [])
            group_by[invoice_line_account].append(
                (invoice_line, invoice_line_infos))
        return group_by

    @api.model
    def _get_invoice_line_infos(self, invoice_line, to_currency, date_to):
        from_currency = invoice_line.currency_id
        res = {}
        if not invoice_line.asset_id:
            res = {
                'account': invoice_line.account_id,
                'purchase_date': invoice_line.invoice_id.date_invoice,
                'purchase': invoice_line.price_subtotal_signed,
            }
        elif invoice_line.asset_id.asset_history_ids:
            for history in \
                    invoice_line.asset_id.asset_history_ids.sorted('date_to'):
                if history.date_to.isoformat() > date_to:
                    if history.category_id.asset_in_progress:
                        res = {
                            'account': history.category_id.asset_account_id,
                            'purchase_date': history.purchase_date,
                            'purchase':
                                history.category_id.purchase_value_sign,
                        }
                        break
        if not res and invoice_line.asset_id.category_id.asset_in_progress:
            res = {
                'account': invoice_line.asset_id.asset_account_id,
                'purchase_date': invoice_line.asset_id.purchase_date,
                'purchase': invoice_line.asset_id.purchase_value_sign,
            }
        return self._convert_to_currency(res, from_currency, to_currency)
