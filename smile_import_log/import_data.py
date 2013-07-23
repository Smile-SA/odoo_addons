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

from openerp.osv import orm, fields
from openerp.modules.registry import RegistryManager

from smile_log.db_handler import SmileDBLogger


class SmileImportData(orm.Model):
    _name = 'smile.import_data'

    def _get_logs(self, cr, uid, ids, name, args, context=None):
        res = {}
        for import_log_id in ids:
            res[import_log_id] = self.pool.get('smile.log').search(cr, uid, [
                ('model_name', '=', 'smile.import_data'),
                ('res_id', '=', import_log_id),
            ], context=context)
        return res

    _columns = {
        'create_uid': fields.many2one('res.users', 'Create user', readonly=True),
        'create_date': fields.datetime('Create date', readonly=True),
        'import_fields': fields.text('Imported Fields', readonly=True),
        'model_id': fields.many2one('ir.model', 'Model', readonly=True),

        'log_ids': fields.function(_get_logs, method=True, type='one2many', relation='smile.log', string="Logs"),
    }


class IrModelData(orm.Model):
    _inherit = 'ir.model.data'

    def _update(self, cr, uid, model, module, values, xml_id=False, store=True, noupdate=False,
                mode='init', res_id=False, context=None):
        context = context or {}
        logger = None
        if context.get('import_logger'):
            logger = context['import_logger']
            if 'import_line_number' in context:
                context['import_line_number'] += 1
                if not context['import_line_number'] % 10:
                    logger.info('Importing line %s of model: %s' % (context['import_line_number'], model))
        try:
            res = super(IrModelData, self)._update(cr, uid, model, module, values, xml_id, store,
                                                   noupdate, mode, res_id, context)
        except Exception as e:
            if logger:
                logger.warning(repr(e))
            raise
        return res


origin_load = orm.BaseModel.load


def new_load(self, cr, uid, fields, data, context=None):
    import_data_obj = self.pool.get('smile.import_data')
    import_context = context.copy() if context else {}
    model_ids = self.pool.get('ir.model').search(cr, uid, [('model', '=', self._name)], context=context)
    if not model_ids:
        raise ValueError('Unknown model: %s' % (self._name,))

    with RegistryManager.get(cr.dbname).cursor() as cr2:
        import_id = import_data_obj.create(cr2, uid, {'import_fields': str(fields),
                                                      'model_id': model_ids[0]}, context)
        cr2.commit()
        logger = SmileDBLogger(cr.dbname, 'smile.import_data', import_id, uid)
        import_context['import_logger'] = logger
        import_context['import_line_number'] = 0

    result = origin_load(self, cr, uid, fields, data, import_context)
    if not result['messages']:
        logger.info('Import completed after %s line(s)' % (import_context['import_line_number'],))
    return result

orm.BaseModel.load = new_load
