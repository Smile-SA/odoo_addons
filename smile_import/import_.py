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

import time, logging

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
        'server_action_id': fields.many2one('ir.actions.server', 'Server Action'),
        'test_mode': fields.boolean('Test Mode'),
    }
    
    def create_import(self, cr, uid, ids, context=None):
        if isinstance(ids, (int, long)):
            ids = [ids]
        import_obj = self.pool.get('ir.model.import')
        import_name = context and context.get('import_name', False)
        for template in self.read(cr, uid, ids, ['name', 'test_mode'], context):
            import_id = import_obj.create(cr, uid, {
                'name': import_name or template['name'],
                'import_tmpl_id': template['id'],
                'state': 'running',
                'from_date': time.strftime('%Y-%m-%d %H:%M:%:S'),
            }, context)
            cr.commit()
            try:
                import_obj.process(cr, uid, import_id, context)
                import_obj.write(cr, uid, import_id, {'state': 'done', 'to_date': time.strftime('%Y-%m-%d %H:%M:%:S')}, context)
            except Exception, e:
                logger = logging.getLogger("smile_import")
                logger.critical("Import failed: %s" % (str(e),), {'import_id': import_id})
                import_obj.write(cr, uid, import_id, {'state': 'exception'}, context)
            
            if template['test_mode']:
                cr.rollback()
                import_obj.write(cr, uid, import_id, {'state': 'draft', 'to_date': False}, context)
                
            cr.commit()
        return True

    def create_server_action(self, cr, uid, ids, context=None):
        if isinstance(ids, (int, long)):
            ids = [ids]
        model_id = self.pool.get('ir.model').search(cr, uid, [('model', '=', self._name)], limit=1, context=context)
        if model_id:
            model_id = model_id[0]
            for template in self.browse(cr, uid, ids, context):
                if not template.server_action_id:
                    vals = {
                        'name': template.name,
                        'user_id': 1,
                        'model_id': model_id,
                        'state': 'code',
                        'code': "self.pool.get('ir.model.import.template').create_import(cr, uid, %d, context)" % (template.id,),
                    }
                    server_action_id = self.pool.get('ir.actions.server').create(cr, uid, vals)
                    template.write({'server_action_id': server_action_id})
        return True
IrModelImportTemplate()

STATES = [
    ('draft', 'Draft'),
    ('running', 'Running'),
    ('done', 'Done'),
    ('exception', 'Exception'),
]

class IrModelImport(osv.osv):
    _name = 'ir.model.import'
    _description = 'Import'
    
    _order = 'from_date desc'

    _columns = {
        'name': fields.char('Name', size=64, readonly=True),
        'import_tmpl_id': fields.many2one('ir.model.import.template', 'Template', readonly=True, ondelete='cascade'),
        'from_date': fields.datetime('From date', readonly=True),
        'to_date': fields.datetime('To date', readonly=True),
        'state': fields.selection(STATES, 'State', size=16, readonly=True),
        'log_ids': fields.one2many('ir.model.import.log', 'import_id', 'Logs', readonly=True),
    }

    defaults = {
        'state': 'draft',
    }

    def process(self, cr, uid, ids, context=None):
        if isinstance(ids, (int, long)):
            ids = [ids]
        context = context or {}
        for import_ in self.browse(cr, uid, ids, context):
            model_obj = self.pool.get(import_.import_tmpl_id.model)
            model_method = import_.import_tmpl_id.method
            context['import_id'] = import_.id
            getattr(model_obj, model_method)(cr, uid, context)
        return True
IrModelImport()

class IrModelImportLog(osv.osv):
    _name = 'ir.model.import.log'
    _description = 'Import Log'
    _rec_name = 'message'
    
    _order = 'create_date desc'

    _columns = {
        'create_date': fields.datetime('Date', readonly=True),
        'import_id': fields.many2one('ir.model.import', 'Import', readonly=True, ondelete='cascade'),
        'level': fields.char('Level', size=16, readonly=True),
        'message': fields.text('Message', readonly=True),
    }
IrModelImportLog()
