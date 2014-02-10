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

import logging

from openerp.osv import orm, fields

_logger = logging.getLogger(__package__)


class IrModel(orm.Model):
    _inherit = 'ir.model'

    @staticmethod
    def _get_function_fields_to_check(models):
        fields_to_check = {}
        for model in models:
            for field in model._columns:
                if isinstance(model._columns[field], (fields.function, fields.related)) and model._columns[field].store:
                    fields_to_check.setdefault(model._name, []).append(field)
        return fields_to_check

    @staticmethod
    def _get_many2one_fields(obj, fields_to_read):
        m2o_fields = []
        for field in fields_to_read:
            if obj._columns[field]._type == 'many2one':
                m2o_fields.append(field)
        return m2o_fields

    @staticmethod
    def _sorted(vals_list):
        return sorted(vals_list, key=lambda x: x['id'])

    def _check_function_fields(self, cr, uid, fields_to_check, context=None):
        invalid_fields = {}
        for model, fields_to_read in sorted(fields_to_check.items()):
            obj = self.pool.get(model)
            ids = obj.search(cr, uid, [], context=context)
            if not ids:
                continue
            classic_write = IrModel._sorted(obj.read(cr, uid, ids, fields_to_read, context, '_classic_write'))
            classic_read = IrModel._sorted(obj.read(cr, uid, ids, fields_to_read, context, '_classic_read'))
            for m2o_field in IrModel._get_many2one_fields(obj, fields_to_read):
                for vals in classic_read:
                    if vals[m2o_field]:
                        vals[m2o_field] = vals[m2o_field][0]
            if classic_write != classic_read:
                invalid_fields[model] = {}
                for write, read in zip(classic_write, classic_read):
                    if write != read:
                        _logger.debug('_classic_write=%s != _classic_read=%s' % (write, read))
                        for field in read:
                            if read[field] != write[field]:
                                invalid_fields[model].setdefault(field, []).append(read['id'])
                _logger.error("Invalidation problems detected for the following fields of the model %s: %s"
                              % (model, invalid_fields[model]))
            else:
                _logger.info("No invalidation problems detected for the following fields of the model %s: %s"
                             % (model, fields_to_read))
        return invalid_fields

    def get_wrong_field_invalidations(self, cr, uid, ids=None, context=None):
        if isinstance(ids, (int, long)):
            ids = ids
        if not ids:
            ids = self.search(cr, uid, [], context=context)
        models = []
        for model in self.browse(cr, uid, ids, context):
            if model.osv_memory:
                continue
            if self.pool.get(model.model):
                models.append(self.pool.get(model.model))
            else:
                _logger.warning("%s model not in pool" % model.model)
        fields_to_check = IrModel._get_function_fields_to_check(models)
        return self._check_function_fields(cr, uid, fields_to_check, context)
