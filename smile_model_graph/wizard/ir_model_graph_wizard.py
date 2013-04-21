# -*- encoding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2013 Smile (<http://www.smile.fr>). All Rights Reserved
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

from osv import fields, orm


class IrModelGraphWizard(orm.TransientModel):
    _name = 'ir.model.graph_wizard'
    _description = 'Model Graph Wizard'

    _columns = {
        'deep': fields.integer('Deep', required=True),
        'show_relation_name': fields.boolean('Show Relation Name'),
        'file': fields.binary('File', filename='filename', readonly=True),
        'filename': fields.char('Filename', size=64, required=True),
    }

    _defaults = {
        'deep': 1,
        'filename': 'model_graph.png',
    }

    def button_generate_file(self, cr, uid, ids, context=None):
        context = context or {}
        model_obj = self.pool.get('ir.model')
        for wizard in self.browse(cr, uid, ids, context):
            data = model_obj.get_graph(cr, uid, context.get('active_ids', []), deep=wizard.deep,
                                       show_relation_name=wizard.show_relation_name, path=None,
                                       context=context)
            wizard.write({'file': data})
        return True
