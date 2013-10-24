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


class SartreExecution(orm.Model):
    _name = 'sartre.execution'
    _description = 'Action Trigger Execution'
    _rec_name = 'trigger_id'

    _columns = {
        'trigger_id': fields.many2one('sartre.trigger', 'Trigger', required=False, select=True, ondelete='cascade'),
        'model_id': fields.many2one('ir.model', 'Object', required=False, select=True),
        'res_id': fields.integer('Resource', required=False),
        'executions_number': fields.integer('Executions'),
    }

    def update_executions_counter(self, cr, uid, trigger, res_id):
        """Update executions counter"""
        if not (trigger and res_id):
            raise orm.except_orm(_('Error'), _('Action Trigger Execution: all arguments are mandatory !'))
        log_id = self.search(cr, uid, [('trigger_id', '=', trigger.id), ('model_id', '=', trigger.model_id.id), ('res_id', '=', res_id)], limit=1)
        if log_id:
            executions_number = self.read(cr, uid, log_id[0], ['executions_number'])['executions_number'] + 1
            return self.write(cr, uid, log_id[0], {'executions_number': executions_number})
        else:
            return self.create(cr, uid, {'trigger_id': trigger.id, 'model_id': trigger.model_id.id,
                                         'res_id': res_id, 'executions_number': 1}) and True
