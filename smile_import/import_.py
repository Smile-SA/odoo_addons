# -*- encoding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution    
#    Copyright (C) 2011 Smile (<http://www.smile.fr>). All Rights Reserved
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

from osv import osv, fields

class IrModelImportTemplate(osv.osv):
    _name = 'ir.model.import.template'
    _description = 'Import Template'

    _columns = {
        'name': fields.char('Name', size=64, required=True),
        'model_id': fields.many2one('ir.model', 'Object', required=True, ondelete='cascade'),
        'model': fields.related('model_id', 'model', type='char', string='Model', readonly=True),
        'method': fields.char('Method', size=64, help="Arguments passed through **kwargs", required=True),
        'import_ids': fields.one2many('ir.model.import', 'import_tmpl_id', 'Imports', readonly=True),
    }
IrModelImportTemplate()

class IrModelImportState(osv.osv):
    _name = 'ir.model.import.state'
    _description = 'Import State'

    _columns = {
        'name': fields.char('Name', size=32, readonly=True),
    }
IrModelImportState()

class IrModelImport(osv.osv):
    _name = 'ir.model.import'
    _description = 'Import'

    _columns = {
        'name': fields.char('Name', size=64, readonly=True),
        'import_tmpl_id': fields.many2one('ir.model.import.template', 'Template', readonly=True, ondelete='cascade'),
        'from_date': fields.datetime('From date', readonly=True),
        'to_date': fields.datetime('To date', readonly=True),
        'state': fields.many2one('ir.model.import.state', 'State', readonly=True),
        'log_ids': fields.one2many('ir.model.import.log', 'import_id', 'Logs', readonly=True),
    }
IrModelImport()

class IrModelImportLog(osv.osv):
    _name = 'ir.model.import.log'
    _description = 'Import Log'
    _rec_name = 'message'

    _columns = {
        'create_date': fields.datetime('Date', readonly=True),
        'import_id': fields.many2one('ir.model.import', 'Import', readonly=True, ondelete='cascade'),
        'level': fields.char('Level', size=16, readonly=True),
        'message': fields.text('Message', readonly=True),
    }
IrModelImportLog()
