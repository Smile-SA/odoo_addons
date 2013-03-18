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

import logging

try:
    from mako.template import Template as MakoTemplate
except ImportError:
    logging.getLogger("import").exception("Mako package is not installed!")

from osv import osv, fields
from tools.func import wraps
from tools.translate import _


class AnalyticJournalView(osv.osv):
    _name = "account.analytic.journal.view"
    _description = "Analytic Journal View"

    _columns = {
        'name': fields.char('Name', size=64, required=True),
        'column_ids': fields.one2many('account.analytic.journal.view.column', 'view_id', 'Columns'),
        'group_ids': fields.many2many('res.groups', 'account_analytic_journal_view_groups_rel', 'view_id', 'group_id', 'Groups'),
        'tree_view_id': fields.many2one('ir.ui.view', 'Tree View', domain=[('type', '=', 'tree')], readonly=True),
        'search_view_id': fields.many2one('ir.ui.view', 'Search View', domain=[('type', '=', 'search')], readonly=True),
    }

    _order = "name"

    _tree_view_template = """
<tree string="Analytic Lines" editable="top">
    % for column in columns:
        <field name="${column.field_id.name}" string="${column.name}" required="${int(column.required)}" readonly="${int(column.readonly)}"/>
    % endfor
</tree>
"""

    _search_view_template = """
<%
    searchable_columns = [column for column in columns if column.searchable]
    extended_filter_columns = [column for column in columns if column.extended_filter]
    groupable_columns = [column for column in columns if column.groupable]
%>
<search string="Analytic Lines">
    % for column in searchable_columns:
        <field name="${column.field_id.name}" string="${column.name}"/>
    % endfor
    % if extended_filter_columns:
        <newline/>
        <group expand="0" string="Extended..." groups="base.group_extended" colspan="${len(searchable_columns)}"
                col="${len(extended_filter_columns)}">
            % for column in extended_filter_columns:
                <field name="${column.field_id.name}" string="${column.name}"/>
            % endfor
        </group>
    % endif
    % if groupable_columns:
        <newline/>
        <group expand="0" string="Group By..." groups="base.group_extended">
            % for column in groupable_columns:
                <filter string="${column.name}" domain="[]" context="{'group_by': '${column.field_id.name}'}"/>
            % endfor
        </group>
    % endif
</search>
"""

    def update_or_create_views(self, cr, uid, ids, context=None):
        view_obj = self.pool.get('ir.ui.view')
        if isinstance(ids, (int, long)):
            ids = [ids]
        for journal_view in self.browse(cr, uid, ids, context):
            for view_type in ('tree', 'search'):
                arch = MakoTemplate(getattr(self, '_%s_view_template' % view_type)).render_unicode(columns=journal_view.column_ids)
                field_name = '%s_view_id' % view_type
                field_value = getattr(journal_view, field_name)
                if field_value:
                    field_value.write({'arch': arch}, context)
                else:
                    journal_view.write({field_name: view_obj.create(cr, uid, {
                        'name': 'account.analytic.line.journal_%s_view' % view_type,
                        'model': 'account.analytic.line',
                        'type': view_type,
                        'arch': arch,
                    }, context)}, context)
        return True

    def write(self, cr, uid, ids, vals, context=None):
        res = super(AnalyticJournalView, self).write(cr, uid, ids, vals, context)
        if 'column_ids' in vals:
            self.update_or_create_views(cr, uid, ids, context)
        return res
AnalyticJournalView()


def journal_view_updater(original_method):
    @wraps(original_method)
    def wrapper(self, cr, uid, ids, *args, **kwargs):
        journal_ids = []
        if isinstance(ids, (int, long)):
            ids = [ids]
        for column in self.read(cr, uid, ids, ['view_id'], load='_classic_write'):
            journal_ids.append(column['view_id'])
        res = original_method(self, cr, uid, ids, *args, **kwargs)
        if journal_ids:
            self.pool.get('account.analytic.journal.view').update_or_create_views(cr, uid, list(set(journal_ids)))
        return res
    return wrapper


class AnalyticJournalColumn(osv.osv):
    _name = "account.analytic.journal.view.column"
    _description = "Analytic Journal View Column"

    _columns = {
        'name': fields.char('Column Label', size=64, required=True),
        'field_id': fields.many2one('ir.model.fields', 'Field', required=True,
                                    domain=[('model_id.model', '=', 'account.analytic.line')], ondelete='cascade'),
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

    @journal_view_updater
    def write(self, cr, uid, ids, vals, context=None):
        return super(AnalyticJournalColumn, self).write(cr, uid, ids, vals, context)

    @journal_view_updater
    def unlink(self, cr, uid, ids, context=None):
        return super(AnalyticJournalColumn, self).unlink(cr, uid, ids, context)
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
        'sign': fields.selection([('1', 'Identical'), ('-1', 'Opposite')], 'Coefficent for parent', required=True,
                                 help="You can specify here the coefficient that will be used when consolidating the amount of this case "
                                      "into its parent. For example, set Identical/Opposite if you want to add/substract it."),
        'view_id': fields.many2one('account.analytic.journal.view', 'Display Mode',
                                   help="Gives the view used when writing or browsing entries in this journal. The view tells OpenERP which "
                                        "fields should be visible, required or readonly and in which order. You can create your own view for "
                                        "a faster encoding in each journal."),
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
        journal = self.browse(cr, uid, journal_id, context)
        res = {
            'type': 'ir.actions.act_window',
            'name': journal.name,
            'res_model': 'account.analytic.line',
            'view_type': 'form',
            'view_mode': 'tree, form',
            'view_id': journal.view_id and journal.view_id.tree_view_id and (journal.view_id.tree_view_id.id, 'default') or False,
            'search_view_id': journal.view_id and journal.view_id.search_view_id and (journal.view_id.search_view_id.id, 'default') or False,
            'domain': "[('journal_id', 'child_of', %s)]" % journal.id,
        }
        context = context or {}
        if context.get('target'):
            res['target'] = 'new'
        return res

    def create_menu(self, cr, uid, ids, context=None):
        try:
            dummy, parent_id = self.pool.get('ir.model.data').get_object_reference(cr, uid, 'account', 'account_analytic_journal_entries')
        except Exception:
            raise osv.except_osv(_('Error'), _('The menu [xml_id=account.account_analytic_journal_entries] is not found!'))
        if isinstance(ids, (int, long)):
            ids = [ids]
        for journal in self.browse(cr, uid, ids, context):
            action_window_vals = self.open_window(cr, uid, journal.id, context)
            for field in ('view_id', 'search_view_id'):
                if isinstance(action_window_vals[field], tuple):
                    action_window_vals[field] = action_window_vals[field][0]
            action_window_id = self.pool.get('ir.actions.act_window').create(cr, uid, action_window_vals, context)
            menu_id = self.pool.get('ir.ui.menu').create(cr, uid, {
                'name': action_window_vals['name'],
                'parent_id': parent_id,
                'action': 'ir.actions.act_window, %s' % action_window_id,
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
                res[analytic_line['id']] = currency_obj.compute(cr, uid, company_currency_id, analytic_line['currency_id'][0],
                                                                analytic_line['amount'], context=context)
            else:
                res[analytic_line['id']] = analytic_line['amount']
        return res

    _columns = {
        'amount_currency': fields.function(_get_amount_currency, method=True, type='float', string='Amount currency', store={
            'account.analytic.line': (lambda self, cr, uid, ids, context=None: ids, ['amount', 'date', 'account_id', 'move_id'], 10),
        }, help="The amount expressed in the related account currency if not equal to the company one.", readonly=True),
    }

    def create(self, cr, uid, vals, context=None):
        if not vals.get('journal_id'):
            raise osv.except_osv(_('Error!'), _('Field journal_id is mandatory to create analytic lines'))
        vals['amount'] *= int(self.pool.get('account.analytic.journal').read(cr, uid, vals['journal_id'], ['sign'], context)['sign'])
        return super(AnalyticLine, self).create(cr, uid, vals, context)
AnalyticLine()
