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

from osv import fields, osv, orm
from lxml import etree
from tools.translate import _
import netsvc
import operator, datetime

SYMBOL_SIZE = 16

class abc_indicator(osv.osv):
    _name = 'abc.indicator'
    
    _cache_models = None
        
    def get_cache_models(self, cr, uid, context={}):
        if self._cache_models is None:
            self.refresh_cache_models(cr, uid, context)
        return self._cache_models
    
    def refresh_cache_models(self, cr, uid, context={}):
        indicator_ids = self.search(cr, uid, [('display_tree', '=', True)], context=context)
        self._cache_models = dict([(indicator.model_id.model, (indicator.field_id.name, indicator.field_id.field_description, indicator.abc_field_id.name)) for indicator in self.browse(cr, uid, indicator_ids, context=context)])
    
    def reload_cache_models(fn):
        """
        Decorator that forces cache models refresh.
        """
        def inner_reload(self, cr, uid, *args):
            fn_res = fn(self, cr, uid, *args)
            self.refresh_cache_models(cr, uid, args[-1]) #context is the last 'arg'
            return fn_res
        return inner_reload

    _columns = {
        'id' :                      fields.integer('Id'),
        'name' :                    fields.char('Name', size=32, required=True,),
        'model_id' :                fields.many2one('ir.model', 'Model', required=True,),
        'field_id' :                fields.many2one('ir.model.fields', 'Field', required=True,),
        'abc_field_id' :            fields.many2one('ir.model.fields', 'ABC Field', readonly=True, on_delete='cascade'),
        'symbol_ids' :              fields.one2many('abc.symbol', 'indicator_id', 'Letters'),
        'display_tree' :            fields.boolean('Display Tree', help="Add the ABC indicator field on tree views"),
        'active' :                  fields.boolean('Active'),
        'last_computation_date' :   fields.date('Last Computation Date'),
    }
    _defaults = {
        'display_tree' :    lambda * a : False,
        'active' :          lambda * a : True,
    }

    @reload_cache_models
    def create(self, cr, uid, vals, context={}):
        technical_name = 'x_abc_%s' % self.pool.get('ir.model.fields').browse(cr, uid, vals['field_id'], context).name
        abc_field_id = self.pool.get('ir.model.fields').create(cr, uid, {
            'name' : technical_name,
            'model_id' : vals['model_id'],
            'state' : 'manual',
            'ttype' : 'many2one',
            'relation' : 'abc.symbol'
        }, context)
        vals.update({'abc_field_id' : abc_field_id})
        return super(abc_indicator, self).create(cr, uid, vals, context)

    @reload_cache_models
    def write(self, cr, uid, ids, vals, context={}):
        res_write = super(abc_indicator, self).write(cr, uid, ids, vals, context)
        if not context.get('write_no_abc_compute', False):
            self.action_compute(cr, uid, ids, context)
        return res_write

    @reload_cache_models
    def unlink(self, cr, uid, ids, context={}):
        return super(abc_indicator, self).unlink(cr, uid, ids, context)

    def compute_all(self, cr, uid, context={}):
        """
        This method (re-)computes every active ABC indicators. Ideally, this method could be called by
        an ir.cron scheduler.
        """
        indicator_ids = self.search(cr, uid, [('active', '=', True)], context)
        return self.action_compute(cr, uid, indicator_ids, context)

    def action_compute(self, cr, uid, indicator_ids, context={}):
        if isinstance(indicator_ids, (int, long)):
            indicator_ids = [indicator_ids]
        new_context = context.copy()
        new_context['write_no_abc_compute'] = True
        for indicator_id in indicator_ids:
            self._compute_indicator(cr, uid, indicator_id, new_context)

    def _compute_indicator(self, cr, uid, indicator_id, context):
        indicator = self.browse(cr, uid, indicator_id, context)

        field_name = indicator.field_id.name
        symbols = indicator.symbol_ids
        
        if not symbols: return
        
        res_ids = self.pool.get(indicator.model_id.model).search(cr, uid, [], context=context)
        res = [(item['id'], item[field_name]) for item in self.pool.get(indicator.model_id.model).read(cr, uid, res_ids, [field_name], context)]
        #cannot use "order=''" search parameter, because of non-stored function fields
        res.sort(lambda l1, l2 : -cmp(l1[1], l2[1]))
        #if min values < 0, add on offset to all values (values must be > 0)
        if res[-1][1] < 0:
            res = map(lambda a, b : a, (b + res[-1][1]), res)
        sum = reduce(operator.add, map(lambda (id, value) : value, res), 0)

        total = 0
        symbol_idx = 0
        for res_line in res:
            total = total + res_line[1]
            symbol = symbols[symbol_idx]
            #self.pool.get('abc.history').create(cr, uid, {'symbol' : symbol.name, 'indicator_id' : indicator_id, 'res_id' : res_line[0]})
            self.pool.get(indicator.model_id.model).write(cr, uid, res_line[0], {indicator.abc_field_id.name : symbol.id}, context)
            if total > (sum * symbol.level / 100):
                symbol_idx += 1
                if symbol_idx > len(symbols) - 1:
                    break
        
        # Other way to prevent concurrency exception ?
        context[self.CONCURRENCY_CHECK_FIELD] = False
        self.write(cr, uid, indicator_id, {'last_computation_date': datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")}, context)
        return True
                
abc_indicator()

def abc_fields_view_get(self, cr, uid, view_id=None, view_type='form', context=None, toolbar=False):
    res = old_fields_view_get(self, cr, uid, view_id, view_type, context, toolbar)

    abc_indicator = self.pool.get('abc.indicator')
    if abc_indicator is not None:
        abc_fields = abc_indicator.get_cache_models(cr, uid, context)
        if abc_fields:
            elm_root = etree.fromstring(res['arch']).getroottree()
            for (model_name, (field_name, field_description, field_technical_name)) in abc_fields.items():
                if self._name == model_name:
                    for elm_field in elm_root.getroot().findall('field[@name="%s"]' % field_name):
                        elm_abc_field = etree.Element('field')
                        elm_abc_field.attrib["name"] = field_technical_name
                        
                        # inutile de rajouter l'attribut groups, il est normalement géré dans le fields_view_get
                        # => TODO: cacher le groupe et ne rajouter le field dans la vue que si l'utilisateur appartient à un des 2 groupes
                        #elm_abc_field.attrib["groups"] = "smile_abc.group_abc_user"
                        
                        elm_field.addnext(elm_abc_field)
                        res['fields'].update({field_technical_name : {'select' : '2', 'type' : 'many2one', 'relation' : 'abc.symbol', 'string' : 'ABC %s' % res['fields'][field_name]['string'], 'readonly' : True, }})
                
            res['arch'] = etree.tostring(elm_root)
    
    return res

old_fields_view_get = orm.orm.fields_view_get
orm.orm.fields_view_get = abc_fields_view_get

class abc_symbol(osv.osv):
    _name = 'abc.symbol'
    _order = 'level'
    
    _columns = {
        'indicator_id' :    fields.many2one('abc.indicator', 'ABC Indicator', on_delete='cascade'),
        'level' :           fields.integer('Level', help='Threshold percentage (between 0 and 100).', required=True,),
        'name' :          fields.char('Name', size=SYMBOL_SIZE, required=True),
    }

    def _check_level(self, cr, uid, symbol_ids):
        for letter_obj in self.browse(cr, uid, symbol_ids):
            if letter_obj.level < 1 or letter_obj.level > 100:
                return False
        return True

    _constraints = [
        (_check_level, _('Level must belong to range [1-100]'), ['level']),
    ]

abc_symbol()

#class abc_history(osv.osv):
#    _name = 'abc.history'
#    _rec_name = 'symbol'
#
#    _columns = {
#        'symbol' :          fields.char('Symbol', size=SYMBOL_SIZE),
#        'indicator_id' :    fields.many2one('abc.indicator', 'ABC Indicator', on_delete='cascade'),
#        'res_id' :          fields.integer('Resource ID'),
#    }
#
#abc_history()
