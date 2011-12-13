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

from osv import osv, fields
from tools.translate import _

class AnalyticJournalView(osv.osv):
    _name = "account.analytic.journal.view"
    _description = "Analytic Journal View"

    _columns = {
        'name': fields.char('Name', size=64, required=True),
        'column_ids': fields.one2many('account.analytic.journal.view.column', 'view_id', 'Columns'),
        'group_ids': fields.many2many('res.groups', 'account_analytic_journal_view_groups_rel', 'view_id', 'group_id', 'Groups'),
    }

    _order = "name"
AnalyticJournalView()

class AnalyticJournalColumn(osv.osv):
    _name = "account.analytic.journal.view.column"
    _description = "Analytic Journal View Column"

    _columns = {
        'name': fields.char('Column Label', size=64, required=True),
        'field_id': fields.many2one('ir.model.fields', 'Field', required=True, domain=[('model_id.model', '=', 'account.analytic.line')], ondelete='cascade'),
        'view_id': fields.many2one('account.journal.view', 'Journal View', select=True, required=True, ondelete='cascade'),
        'sequence': fields.integer('Sequence', help="Gives the sequence order to journal column.", required=True),
        'required': fields.boolean('Required'),
        'readonly': fields.boolean('Readonly'),
        'searchable': fields.boolean('Searchable'),
        'extended_filter': fields.boolean('Searchable via extended filters'),
        'groupable': fields.boolean('Groupable'),
    }

    _defaults = {
        'searchable': True,
    }

    _order = "view_id, sequence"

    def onchange_field_id(self, cr, uid, ids, field_id, context=None):
        res = {}
        if field_id:
            field = self.pool.get('ir.model.fields').read(cr, uid, field_id, ['field_description', 'required', 'readonly'], context)
            res['value'] = {
                'name': field['field_description'],
                'required': field['required'],
                'readonly': field['readonly'],
            }
        return res
AnalyticJournalColumn()

class AnalyticJournal(osv.osv):
    _inherit = "account.analytic.journal"
    _parent_store = True

    def __init__(self, pool, cr):
        super(AnalyticJournal, self).__init__(pool, cr)
        self._columns['type'].selection.append(('view', 'View'))

    def _get_complete_name(self, cr, uid, ids, name, args, context=None):

        def _get_one_full_name(journal):
            parent_path = journal.parent_id and '%s > ' % _get_one_full_name(journal.parent_id) or ''
            return parent_path + journal.name

        res = {}
        for journal in self.browse(cr, uid, ids, context):
            res[journal.id] = _get_one_full_name(journal)
        return res

    _columns = {
        'sign': fields.selection([('1', 'Identical'), ('-1', 'Opposite')], 'Sign compared to original records', required=True),
        'view_id': fields.many2one('account.analytic.journal.view', 'Display Mode', help="Gives the view used when writing or browsing entries in this journal. The view tells OpenERP which fields should be visible, required or readonly and in which order. You can create your own view for a faster encoding in each journal."),
        'menu_id': fields.many2one('ir.ui.menu', 'Menu', help="To access to display mode view"),
        'parent_id': fields.many2one('account.analytic.journal', 'Parent', ondelete='cascade'),
        'child_ids': fields.one2many('account.analytic.journal', 'parent_id', 'Children'),
        'parent_left': fields.integer('Parent Left', select=1),
        'parent_right': fields.integer('Parent Right', select=1),
        'complete_name': fields.function(_get_complete_name, method=True, type='char', size=256, string="Name"),
    }

    _defaults = {
        'sign': '1',
    }

    def open_window(self, cr, uid, journal_id, context=None):
        if isinstance(journal_id, (list, tuple)):
            journal_id = journal_id[0]
        journal = self.read(cr, uid, journal_id, ['name', 'view_id'], context)
        res = {
            'type': 'ir.actions.act_window',
            'name': journal['name'],
            'res_model': 'account.analytic.line',
            'view_type': 'form',
            'view_mode': 'tree,form',
            'domain': "[('journal_id', 'child_of', %s)]" % journal_id,
            'context': "{'journal_view_id': %s}" % (journal['view_id'] and journal['view_id'][0],),
        }
        context = context or {}
        if context.get('target'):
            res['target'] = 'new'
        return res

    def create_menu(self, cr, uid, ids, context=None):
        try:
            dummy, parent_id = self.pool.get('ir.model.data').get_object_reference(cr, uid, 'account', 'account_analytic_journal_entries')
        except:
            raise osv.except_osv(_('Error'), _('The menu [xml_id=account.account_analytic_journal_entries] is not found!'))
        if isinstance(ids, (int, long)):
            ids = [ids]
        for journal in self.browse(cr, uid, ids, context):
            action_window_vals = self.open_window(cr, uid, journal.id, context)
            action_window_id = self.pool.get('ir.actions.act_window').create(cr, uid, action_window_vals, context)
            menu_id = self.pool.get('ir.ui.menu').create(cr, uid, {
                'name': action_window_vals['name'],
                'parent_id': parent_id,
                'action': 'ir.actions.act_window,%s' % action_window_id,
                'groups_id': [(6, 0, [group.id for group in journal.view_id.group_ids])],
            }, context)
            journal.write({'menu_id': menu_id}, context)
        return True
AnalyticJournal()

class AnalyticLine(osv.osv):
    _inherit = 'account.analytic.line'

    def __init__(self, pool, cr):
        super(AnalyticLine, self).__init__(pool, cr)
        self._columns['journal_id']._domain.append(('type', '!=', 'view'))

    def _get_amount_currency(self, cr, uid, ids, name, arg, context=None):
        res = {}
        context = context or {}
        company_obj = self.pool.get('res.company')
        currency_obj = self.pool.get('res.currency')
        if isinstance(ids, (int, long)):
            ids = [ids]
        for analytic_line in self.read(cr, uid, ids, ['amount', 'date', 'currency_id', 'company_id'], context):
            if analytic_line['currency_id'] and analytic_line['company_id']:
                context['date'] = analytic_line['date']
                company_currency_id = company_obj.read(cr, uid, analytic_line['company_id'][0], ['currency_id'], context)['currency_id'][0]
                res[analytic_line['id']] = currency_obj.compute(cr, uid, company_currency_id, analytic_line['currency_id'][0], analytic_line['amount'], context=context)
            else:
                res[analytic_line['id']] = analytic_line['amount']
        return res

    _columns = {
        'amount_currency': fields.function(_get_amount_currency, method=True, type='float', string='Amount currency', store={
            'account.analytic.line': (lambda self, cr, uid, ids, context=None: ids, ['amount', 'date', 'account_id', 'move_id'], 10),
        }, help="The amount expressed in the related account currency if not equal to the company one.", readonly=True),
    }

    def create(self, cr, uid, vals, context=None):
        vals['amount'] *= int(self.pool.get('account.analytic.journal').read(cr, uid, vals['journal_id'], ['sign'], context)['sign'])
        return super(AnalyticLine, self).create(cr, uid, vals, context)

    def fields_view_get(self, cr, uid, view_id=None, view_type='form', context=None, toolbar=False, submenu=False):
        res = super(AnalyticLine, self).fields_view_get(cr, uid, view_id, view_type, context, toolbar, submenu)
        context = context or {}
        if context.get('journal_view_id') and view_type in ('tree', 'search'):
            columns = self.pool.get('account.analytic.journal.view').browse(cr, uid, context['journal_view_id'], context).column_ids
            res['fields'] = self.fields_get(cr, uid, context=context)
            if view_type == 'tree':
                res['arch'] = '<tree string="Analytic Lines" editable="top">\n'
                for column in columns:
                    attrs = ''
                    if column.required:
                        attrs += ' required="1"'
                    if column.readonly:
                        attrs += ' readonly="1"'
                    res['arch'] += '    <field name="%s" string="%s"%s/>\n' % (column.field_id.name, column.name, attrs)
            elif view_type == 'search':
                res['arch'] = '<search string="Analytic Lines">\n'
                searchable_columns = [column for column in columns if column.searchable]
                for column in searchable_columns:
                    res['arch'] += '    <field name="%s" string="%s"/>\n' % (column.field_id.name, column.name)
                extended_filter_columns = [column for column in columns if column.extended_filter]
                if extended_filter_columns:
                    res['arch'] += '    <newline/>\n' \
                                   '    <group expand="0" string="Extended..." groups="base.group_extended" colspan="%s" col="%s">\n' % (len(searchable_columns), len(extended_filter_columns))
                    for column in extended_filter_columns:
                        res['arch'] += '''        <field name="%s" string="%s"/>\n''' % (column.field_id.name, column.name)
                    res['arch'] += '    </group>\n'
                groupable_columns = [column for column in columns if column.groupable]
                if groupable_columns:
                    res['arch'] += '    <newline/>\n' \
                                   '    <group expand="0" string="Group By..." groups="base.group_extended">\n'
                    for column in groupable_columns:
                        res['arch'] += '''        <filter string="%s" domain="[]" context="{'group_by':'%s'}"/>\n''' % (column.name, column.field_id.name)
                    res['arch'] += '    </group>\n'
            res['arch'] += '</%s>' % view_type
        return res
AnalyticLine()
