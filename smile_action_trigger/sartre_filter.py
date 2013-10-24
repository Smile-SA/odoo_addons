# -*- encoding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2010 Smile (<http://www.smile.fr>). All Rights Reserved
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

from openerp.osv import orm, fields
from openerp.tools.translate import _


class SartreFilter(orm.Model):
    _name = 'sartre.filter'
    _description = 'Action Trigger Filter'
    _rec_name = 'field_id'

    def onchange_get_domain(self, cr, uid, ids, field='', operator_id=False, opposite=False,
                            value='', value_age='current', value_type='static', context=None):
        """Build domain expression from filter items"""
        res = {}
        operator_pool = self.pool.get('sartre.operator')
        if field and operator_id and (value or not operator_pool.read(cr, uid, operator_id, ['other_value_necessary'])['other_value_necessary']):
            field_name = (value_age == 'old' and 'OLD_' or '') + field
            operator_inst = operator_pool.browse(cr, uid, operator_id)
            symbol = opposite and operator_inst.opposite_symbol or operator_inst.symbol
            if value_age == 'current' and value_type == 'static':
                value = operator_inst.other_value_transformation and eval(operator_inst.other_value_transformation, {'value': value}) or value
            if value_type == 'dynamic' and value:
                value = '[[ object.' + value + ' ]]'
            res['value'] = {'domain': str([(field_name, symbol, value)])}
        return res

    def _build_field_expression(self, cr, uid, field_id, field_expression='', context=None):
        """Build field expression"""
        field_pool = self.pool.get('ir.model.fields')
        field_obj = field_pool.read(cr, uid, field_id, ['name', 'ttype', 'relation', 'model'])
        field_expr = field_expression and (field_expression.split('.')[:-1]
                                           and '.'.join(field_expression.split('.')[:-1])
                                           or field_expression) + '.' or ''
        obj = self.pool.get(field_obj['model'])
        if field_obj['name'] in obj._columns and 'fields.related' in str(obj._columns[field_obj['name']]):
            field_expr += obj._columns[field_obj['name']].arg[0] + '.'
        field_expr += field_obj['name']
        if field_obj['ttype'] in ['many2one', 'one2many', 'many2many']:
            field_expr += field_obj['ttype'] == 'many2one' and '.' or ''
            field_expr += field_obj['ttype'] in ['one2many', 'many2many'] and '[0].' or ''
            field_expr += self.pool.get(field_obj['relation'])._rec_name
        return field_expr

    def _check_field_expression(self, cr, uid, model_id, field_expression='', context=None):
        """Check field expression"""
        field_list = field_expression and (field_expression.split('.')[:-1] or [field_expression])
        if field_list:
            field_pool = self.pool.get('ir.model.fields')
            model = self.pool.get('ir.model').read(cr, uid, model_id, ['model'])['model']
            for f_name in field_list:
                if '[' in f_name:
                    f_name = f_name[: f_name.index('[')]
                f_id = field_pool.search(cr, uid, [('model', '=', model), ('name', '=', f_name)], limit=1, context=context)
                if not f_id:
                    raise orm.except_orm(_('Error'), _("The field %s is not in the model %s !" % (f_name, model)))
                f_obj = field_pool.read(cr, uid, f_id[0], ['name', 'ttype', 'relation'])
                if f_obj['ttype'] in ['many2one', 'one2many', 'many2many']:
                    model = f_obj['relation']
                    model_id = self.pool.get('ir.model').search(cr, uid, [('model', '=', model)], limit=1, context=context)[0]
                elif len(field_expression.split('.')) > 1:
                    raise orm.except_orm(_('Error'), _("The field %s is not a relation field !" % f_obj['name']))
        return model_id

    def onchange_get_field_domain(self, cr, uid, ids, model_id, field_expression='', context=None):
        """Get field domain"""
        model_id = self._check_field_expression(cr, uid, model_id, field_expression, context)
        return {'value': {'field_id': False}, 'domain': {'field_id': "[('model_id', '=', %d)]" % model_id}}

    def onchange_get_field_expression(self, cr, uid, ids, model_id, field_expression='', field_id=False, context=None):
        """Update the field expression"""
        if field_id:
            field_expression = self._build_field_expression(cr, uid, field_id, field_expression, context)
        res = self.onchange_get_field_domain(cr, uid, ids, model_id, field_expression, context)
        res.setdefault('value', {}).update({'field_expression': field_expression})
        return res

    def onchange_get_value_age_domain(self, cr, uid, ids, field='', operator_id=False,
                                      opposite=False, value='', value_age='current', value_type='static', context=None):
        """Update the field 'value_age'"""
        value_age_filter = operator_id and self.pool.get('sartre.operator').read(cr, uid, operator_id, ['value_age_filter'])['value_age_filter']
        if value_age_filter != 'both':
            value_age = value_age_filter
        res = self.onchange_get_domain(cr, uid, ids, field, operator_id, opposite, value, value_age, value_type, context)
        res.setdefault('value', {})
        res['value'] = {'value_age': value_age, 'value_age_readonly': value_age_filter != 'both'}
        return res

    _columns = {
        "trigger_id": fields.many2one('sartre.trigger', "Trigger", required=True, ondelete='cascade'),
        "field_name": fields.char("Field", size=256),
        "value_age": fields.selection([
            ('current', 'Current Value'),
            ('old', 'Old Value'),
        ], "Value Age", select=True),
        "value_age_readonly": fields.boolean("Value Age Readonly"),
        "operator_id": fields.many2one('sartre.operator', "Operator"),
        "opposite": fields.boolean('Opposite'),
        "value": fields.char("Value", size=128, help="Dynamic value corresponds to an object field"),
        "value_type": fields.selection([('static', 'Static'), ('dynamic', 'Dynamic')], "Value Type"),
        "domain": fields.char("Domain", size=256, required=True),
        "field_id": fields.many2one('ir.model.fields', "Field Builder"),
        "field_expression": fields.char("Expression to copy", size=256),
    }

    _defaults = {
        'value_age': 'current',
        'value_type': 'static',
    }
