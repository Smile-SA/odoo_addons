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

import pickle

from openerp.osv import orm

from openerp.osv.orm import fix_import_export_id_paths

from openerp.tools.config import config

from openerp.tools.misc import CountingStream


def import_data_custom(self, cr, uid, fields, datas, mode='init', current_module='', noupdate=False, context=None, filename=None):
    """
    .. deprecated:: 7.0
        Use :meth:`~load` instead

    Import given data in given module

    This method is used when importing data via client menu.

    Example of fields to import for a sale.order::

        .id,                         (=database_id)
        partner_id,                  (=name_search)
        order_line/.id,              (=database_id)
        order_line/name,
        order_line/product_id/id,    (=xml id)
        order_line/price_unit,
        order_line/product_uom_qty,
        order_line/product_uom/id    (=xml_id)

    This method returns a 4-tuple with the following structure::

        (return_code, errored_resource, error_message, unused)

    * The first item is a return code, it is ``-1`` in case of
      import error, or the last imported row number in case of success
    * The second item contains the record data dict that failed to import
      in case of error, otherwise it's 0
    * The third item contains an error message string in case of error,
      otherwise it's 0
    * The last item is currently unused, with no specific semantics

    :param fields: list of fields to import
    :param datas: data to import
    :param mode: 'init' or 'update' for record creation
    :param current_module: module name
    :param noupdate: flag for record creation
    :param filename: optional file to store partial import state for recovery
    :returns: 4-tuple in the form (return_code, errored_resource, error_message, unused)
    :rtype: (int, dict or 0, str or 0, str or 0)
    """

    context = dict(context) if context is not None else {}
    context['_import_current_module'] = current_module
    import_partial = context.get('import_partial')

    fields = map(fix_import_export_id_paths, fields)
    ir_model_data_obj = self.pool.get('ir.model.data')
    logs = []
    def log(m):
        if m['type'] == 'error':
            raise Exception(m['message'])

    nb_imported = 0
    for res_id, xml_id, res, info, log_error in self._convert_records_custom(cr, uid,
                    self._extract_records(cr, uid, fields, datas,
                                          context=context, log=log),
                    context=context, log=log):
        if log_error:
            logs.append(log_error)
            continue
        try:
            ir_model_data_obj._update(cr, uid, self._name,
                 current_module, res, mode=mode, xml_id=xml_id,
                 noupdate=noupdate, res_id=res_id, context=context)
            if import_partial:
                cr.commit()
                nb_imported += 1
        except Exception, e:
            logs.append(e)

    if logs and not import_partial:
        cr.rollback()

    return nb_imported, logs

orm.Model.import_data_custom = import_data_custom


def _convert_records_custom(self, cr, uid, records,
                     context=None, log=lambda a: None):
    """ Converts records from the source iterable (recursive dicts of
    strings) into forms which can be written to the database (via
    self.create or (ir.model.data)._update)

    :returns: a list of triplets of (id, xid, record)
    :rtype: list((int|None, str|None, dict))
    """

    if context is None: context = {}
    Converter = self.pool['ir.fields.converter']
    columns = dict((k, v.column) for k, v in self._all_columns.iteritems())
    Translation = self.pool['ir.translation']
    field_names = dict(
        (f, (Translation._get_source(cr, uid, self._name + ',' + f, 'field',
                                     context.get('lang'))
             or column.string))
        for f, column in columns.iteritems())

    convert = Converter.for_model(cr, uid, self, context=context)

    def _log(base, field, exception):
        type = 'warning' if isinstance(exception, Warning) else 'error'
        # logs the logical (not human-readable) field name for automated
        # processing of response, but injects human readable in message
        record = dict(base, type=type, field=field,
                      message=unicode(exception.args[0]) % base)
        if len(exception.args) > 1 and exception.args[1]:
            record.update(exception.args[1])
        log(record)

    stream = CountingStream(records)
    for record, extras in stream:
        log_error = ''
        converted = {}
        dbid = False
        xid = False
        # name_get/name_create
        if None in record: pass
        # xid
        if 'id' in record:
            xid = record['id']
        # dbid
        if '.id' in record:
            try:
                dbid = int(record['.id'])
            except ValueError:
                # in case of overridden id column
                dbid = record['.id']
            if not self.search(cr, uid, [('id', '=', dbid)], context=context):
                log(dict(extras,
                    type='error',
                    record=stream.index,
                    field='.id',
                    message=_(u"Unknown database identifier '%s'") % dbid))
                dbid = False
        try:
            converted = convert(record, lambda field, err:\
                _log(dict(extras, record=stream.index, field=field_names[field]), field, err))
        except Exception, e:
            log_error = e.message

        yield dbid, xid, converted, dict(extras, record=stream.index), log_error

orm.Model._convert_records_custom = _convert_records_custom
