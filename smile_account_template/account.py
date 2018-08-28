# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2011-2012 Smile (<http://www.smile.fr>).
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

import decimal_precision as dp
from osv import osv, fields
from tools.translate import _


class AccountJournalTemplate(osv.osv):
    _name = "account.journal.template"
    _description = "Journal Template"
    _order = 'code'

    _columns = {
        'name': fields.char('Journal Name', size=64, required=True),
        'code': fields.char('Code', size=5, required=True,
                            help="The code will be used to generate the numbers of the journal entries of this journal."),
        'type': fields.selection([('sale', 'Sale'), ('sale_refund', 'Sale Refund'), ('purchase', 'Purchase'),
                                  ('purchase_refund', 'Purchase Refund'), ('cash', 'Cash'), ('bank', 'Bank and Cheques'),
                                  ('general', 'General'), ('situation', 'Opening/Closing Situation')],
                                 'Type', size=32, required=True,
                                 help="Select 'Sale' for Sale journal to be used at the time of making invoice."
                                 " Select 'Purchase' for Purchase Journal to be used at the time of approving purchase order."
                                 " Select 'Cash' to be used at the time of making payment."
                                 " Select 'General' for miscellaneous operations."
                                 " Select 'Opening/Closing Situation' to be used at the time of new fiscal year creation or end"
                                 " of year entries generation."),
        'refund_journal': fields.boolean('Refund Journal', help='Fill this if the journal is to be used for refunds of invoices.'),
        'type_control_ids': fields.many2many('account.account.type', 'account_journal_type_rel', 'journal_id', 'type_id', 'Type Controls',
                                             domain=[('code', '<>', 'view'), ('code', '<>', 'closed')]),
        'account_control_ids': fields.many2many('account.account.template', 'account_account_type_journal_template_rel',
                                                'journal_id', 'account_template_id', 'Accounts', domain=[('type', 'not in', ('view', 'closed'))]),
        'view_id': fields.many2one('account.journal.view', 'Display Mode', required=True,
                                   help="Gives the view used when writing or browsing entries in this journal. The view tells OpenERP which"
                                   " fields should be visible, required or readonly and in which order."
                                   " You can create your own view for a faster encoding in each journal."),
        'default_credit_account_id': fields.many2one('account.account.template', 'Default Credit Account', domain="[('type','!=','view')]",
                                                     help="It acts as a default account for credit amount"),
        'default_debit_account_id': fields.many2one('account.account.template', 'Default Debit Account', domain="[('type','!=','view')]",
                                                    help="It acts as a default account for debit amount"),
        'centralisation': fields.boolean('Centralised counterpart',
                                         help="Check this box to determine that each entry of this journal won't create a new counterpart"
                                         " but will share the same counterpart. This is used in fiscal year closing."),
        'update_posted': fields.boolean('Allow Cancelling Entries',
                                        help="Check this box if you want to allow the cancellation the entries related to"
                                        " this journal or of the invoice related to this journal"),
        'group_invoice_lines': fields.boolean('Group Invoice Lines',
                                              help="If this box is checked, the system will try to group the accounting"
                                              " lines when generating them from invoices."),
        'sequence_id': fields.many2one('ir.sequence.template', 'Entry Sequence',
                                       help="This field contains the informatin related to the numbering"
                                       " of the journal entries of this journal.", required=True),
        'user_id': fields.many2one('res.users', 'User', help="The user responsible for this journal"),
        'groups_id': fields.many2many('res.groups', 'account_journal_group_rel', 'journal_id', 'group_id', 'Groups'),
        'currency': fields.many2one('res.currency', 'Currency', help='The currency used to enter statement'),
        'entry_posted': fields.boolean('Skip \'Draft\' State for Manual Entries',
                                       help='Check this box if you don\'t want new journal entries to pass through the \'draft\' state and instead'
                                       ' goes directly to the \'posted state\' without any manual validation. \nNote that journal entries that are'
                                       ' automatically created by the system are always skipping that state.'),
        'chart_template_id': fields.many2one('account.chart.template', 'Chart Template', required=True, ondelete="cascade"),
        'allow_date': fields.boolean('Check Date not in the Period',
                                     help='If set to True then do not accept the entry if the entry date is not into the period dates'),
        'analytic_journal_id': fields.many2one('account.analytic.journal', 'Analytic Journal', help="Journal for analytic entries"),
    }

    _defaults = {
        'user_id': lambda self, cr, uid, context=None: uid,
    }

    _sql_constraints = [
        ('code_chart_template_uniq', 'UNIQUE(code, chart_template_id)', 'The code of the journal must be unique per chart template!'),
        ('name_chart_template_uniq', 'UNIQUE(name, chart_template_id)', 'The name of the journal must be unique per chart template!'),
    ]

    def onchange_type(self, cr, uid, ids, type, currency, context=None):
        model_data_obj = self.pool.get('ir.model.data')
        user_obj = self.pool.get('res.users')
        type_mapping = {
            'sale': 'account_sp_journal_view',
            'sale_refund': 'account_sp_refund_journal_view',
            'purchase': 'account_sp_journal_view',
            'purchase_refund': 'account_sp_refund_journal_view',
            'cash': 'account_journal_bank_view',
            'bank': 'account_journal_bank_view',
            'general': 'account_journal_view',
            'situation': 'account_journal_view'
        }
        res = {}
        view_id = type_mapping.get(type, 'account_journal_view')
        user = user_obj.browse(cr, uid, uid, context)
        if type in ('cash', 'bank') and currency and user.company_id.currency_id.id != currency:
            view_id = 'account_journal_bank_view_multi'
        data_id = model_data_obj.search(cr, uid, [('model', '=', 'account.journal.view'), ('name', '=', view_id)], context=context)
        data = model_data_obj.browse(cr, uid, data_id[0], context)
        res.update({
            'centralisation': type == 'situation',
            'view_id': data.res_id,
        })
        return {'value': res}

AccountJournalTemplate()


class AccountAccountTemplateByResource(osv.osv):
    _name = 'account.account.template.by_resource'
    _description = "Account Templates by resource"

    def _get_name(self, cr, uid, ids, name, arg, context=None):
        res = {}
        if isinstance(ids, (int, long)):
            ids = [ids]
        for by_resource in self.browse(cr, uid, ids, context):
            res[by_resource.id] = self.pool.get(by_resource.model_id.model).name_get(cr, uid, [by_resource.res_id], context)[0]
        return res

    def _get_root_id(self, cr, uid, account_tmpl):
        if not account_tmpl.parent_id:
            return account_tmpl.id
        return self._get_root_id(cr, uid, account_tmpl.parent_id)

    def _get_chart_template(self, cr, uid, ids, name, arg, context=None):
        res = {}
        if isinstance(ids, (int, long)):
            ids = [ids]
        for account_tmpl in self.browse(cr, uid, ids, context):
            res[account_tmpl.id] = self._get_root_id(cr, uid, account_tmpl.account_id)
        return res

    def _get_account_template_ids_from_chart_template(self, cr, uid, ids, context=None):
        account_template_ids = []
        parents = [chart_tmpl.account_root_id for chart_tmpl in self.browse(cr, uid, ids, context)]
        while parents:
            account_template_ids += [parent.id for parent in parents]
            parents = sum([parent.child_parent_ids for parent in parents], [])
        return self.pool.get('account.account.template.by_resource').search(cr, uid, [('account_id', 'in', account_template_ids)],
                                                                            context=context)

    _columns = {
        'model_id': fields.many2one("ir.model", "Object", required=True),
        'field_id': fields.many2one("ir.model.fields", "Field", required=True, domain=[('ttype', '=', 'many2one')]),
        'res_id': fields.integer('Resource Id', required=True),
        'res_name': fields.function(_get_name, method=True, type='char', string='Resource Name'),
        'account_id': fields.many2one("account.account.template", 'Account Template', required=True,
                                           domain=[('type', 'not in', ('view', 'closed'))]),
        'chart_template_id': fields.function(_get_chart_template, method=True, type='many2one', relation='account.chart.template', store={
            'account.chart.template': (_get_account_template_ids_from_chart_template, ['account_root_id'], 10),
            'account.account.template.by_resource': (lambda self, cr, uid, ids, context=None: ids, ['account_id'], 10),
        }, string='Chart Template'),
    }

    def create(self, cr, uid, vals, context=None):
        res_id = super(AccountAccountTemplateByResource, self).create(cr, uid, vals, context)
        self._store_set_values(cr, uid, [res_id], ['chart_template_id'], context)
        return res_id

    def _get_res_id(self, cr, uid, fields, datas):
        if 'res_id:id' in fields and 'model_id:id' in fields:
            res_id_position = fields.index('res_id:id')
            model_id_position = fields.index('model_id:id')
            model_data_obj = self.pool.get('ir.model.data')
            for data in datas:
                module, xml_id = data[res_id_position].split('.')
                res_model, res_id = model_data_obj.get_object_reference(cr, uid, module, xml_id)
                data_model = data[model_id_position].split('.')[1]
                if res_model.replace('.', '_') != data_model.replace('model_', ''):
                    raise osv.except_osv(_('Error'), _('res_id model and model_id must be identical'))
                data[res_id_position] = res_id
            fields[res_id_position] = 'res_id'

    def import_data(self, cr, uid, fields, datas, mode='init', current_module='', noupdate=False, context=None, filename=None):
        self._get_res_id(cr, uid, fields, datas)
        return super(AccountAccountTemplateByResource, self).import_data(cr, uid, fields, datas, mode, current_module, noupdate, context, filename)

AccountAccountTemplateByResource()


class AccountModelTemplate(osv.osv):
    _name = "account.model.template"
    _description = "Template for Account Model"

    _columns = {
        'name': fields.char('Model Name', size=64, required=True, help="This is a model for recurring accounting entries"),
        'journal_id': fields.many2one('account.journal.template', 'Journal', required=True),
        'lines_id': fields.one2many('account.model.line.template', 'model_id', 'Model Entries'),
        'legend': fields.text('Legend', readonly=True, size=100),
        'chart_template_id': fields.related('journal_id', 'chart_template_id', type='many2one', relation='account.chart.template',
                                            string='Chart Template', readonly=True, ondelete="cascade", store=True),
    }

    _defaults = {
        'legend': lambda self, cr, uid, context: _('You can specify year, month and date in the name of the model using the following'
        ' labels:\n\n%(year)s: To Specify Year \n%(month)s: To Specify Month \n%(date)s: Current Date\n\ne.g. My model on %(date)s'),
    }

AccountModelTemplate()


class AccountModelTemplateLine(osv.osv):
    _name = "account.model.line.template"
    _description = "Template for Account Model Entries"
    _order = 'sequence'

    _columns = {
        'name': fields.char('Name', size=64, required=True),
        'sequence': fields.integer('Sequence', required=True, help="The sequence field is used to order the resources from lower sequences"
                                   " to higher ones"),
        'quantity': fields.float('Quantity', digits_compute=dp.get_precision('Account'), help="The optional quantity on entries"),
        'debit': fields.float('Debit', digits_compute=dp.get_precision('Account')),
        'credit': fields.float('Credit', digits_compute=dp.get_precision('Account')),
        'account_id': fields.many2one('account.account.template', 'Account', required=True, ondelete="cascade"),
        'analytic_account_id': fields.many2one('account.analytic.account', 'Analytic Account'),
        'model_id': fields.many2one('account.model.template', 'Model', required=True, ondelete="cascade", select=True),
        'amount_currency': fields.float('Amount Currency', help="The amount expressed in an optional other currency."),
        'currency_id': fields.many2one('res.currency', 'Currency'),
        'partner_id': fields.many2one('res.partner', 'Partner'),
        'date_maturity': fields.selection([('today', 'Date of the day'), ('partner', 'Partner Payment Term')], 'Maturity date',
                                          help="The maturity date of the generated entries for this model. You can choose between the creation date"
                                          " or the creation date of the entries plus the partner payment terms."),
    }

    _sql_constraints = [
        ('credit_debit1', 'CHECK (credit*debit=0)',  'Wrong credit or debit value in model (Credit Or Debit Must Be "0")!'),
        ('credit_debit2', 'CHECK (credit+debit>=0)', 'Wrong credit or debit value in model (Credit + Debit Must Be greater "0")!'),
    ]

AccountModelTemplateLine()


class AccountChartTemplate(osv.osv):
    _inherit = "account.chart.template"

    _columns = {
        'journal_ids': fields.one2many('account.journal.template', 'chart_template_id', 'Account Journal Templates'),
        'by_resource_ids': fields.one2many('account.account.template.by_resource', 'chart_template_id', 'Account Templates by resource'),
        'account_model_ids': fields.one2many('account.model.template', 'chart_template_id', 'Account Model Templates'),
    }

AccountChartTemplate()
