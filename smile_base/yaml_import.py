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

from dateutil.relativedelta import relativedelta
import logging
from lxml import etree
import time

from openerp import netsvc, pooler, SUPERUSER_ID
from openerp.tools import is_eval, is_ref, is_string, misc, YamlImportException, YamlInterpreter
from openerp.tools.config import config

_logger = logging.getLogger(__name__)

unsafe_eval = eval
native_init = YamlInterpreter.__init__
native_process_node = YamlInterpreter._process_node


def new_init(self, cr, module, id_map, mode, filename, noupdate=False):
    native_init(self, cr, module, id_map, mode, filename, noupdate)
    self.uid = SUPERUSER_ID
    self.eval_context.update({
        'pool': pooler.get_pool(cr.dbname),
        'cr': cr,
        'uid': self.uid,
        'context': None,
        'relativedelta': relativedelta,
        'float': float,
        'int': int,
        'str': str,
    })


def _get_uid(self, yamltag):
    if yamltag.uid is not None:
        uid = yamltag.uid
        if isinstance(uid, basestring):
            uid = self._ref()(uid)
    else:
        uid = self.uid
    return uid


def _eval_field(self, model, field_name, expression, view=False, parent={}, default=True):
    # TODO this should be refactored as something like model.get_field() in bin/osv
    if field_name in model._columns:
        column = model._columns[field_name]
    elif field_name in model._inherit_fields:
        column = model._inherit_fields[field_name][2]
    else:
        raise KeyError("Object '%s' does not contain field '%s'" % (model, field_name))
    if is_ref(expression):
        elements = self.process_ref(expression, column)
        if column._type in ("many2many", "one2many"):
            value = [(6, 0, elements)]
        else:  # many2one
            if isinstance(elements, (list, tuple)):
                value = self._get_first_result(elements)
            else:
                value = elements
    elif column._type == "many2one":
        # Added by Smile #
        if is_eval(expression):
            value = self.process_eval(expression)
        else:
            value = self.get_id(expression)
        ###################
    elif column._type == "one2many":
        other_model = self.get_model(column._obj)
        value = [(0, 0, self._create_record(other_model, fields, view, parent, default=default)) for fields in expression]
    elif column._type == "many2many":
        # Changed by Smile #
        ids = [(self.process_eval(xml_id) if is_eval(xml_id) else self.get_id(xml_id)) for xml_id in expression]
        ####################
        value = [(6, 0, ids)]
    elif column._type == "date" and is_string(expression):
        # enforce ISO format for string date values, to be locale-agnostic during tests
        time.strptime(expression, misc.DEFAULT_SERVER_DATE_FORMAT)
        value = expression
    elif column._type == "datetime" and is_string(expression):
        # enforce ISO format for string datetime values, to be locale-agnostic during tests
        time.strptime(expression, misc.DEFAULT_SERVER_DATETIME_FORMAT)
        value = expression
    else:  # scalar field
        if is_eval(expression):
            value = self.process_eval(expression)
        else:
            value = expression
        # raise YamlImportException('Unsupported column "%s" or value %s:%s' % (field_name, type(expression), expression))
    return value


def new_process_node(self, node):
    max_delay = isinstance(node, dict) and hasattr(node.keys()[0], 'max_delay') and node.keys()[0].max_delay or 0.0
    start = time.time()
    native_process_node(self, node)
    delay = time.time() - start
    if max_delay and delay > max_delay:
        factor = 1000.0
        self._log_assert_failure(logging.ERROR, "Test execution time limit (%s > %s) has been exceeded" % (delay * factor, max_delay * factor))


def new_process_function(self, node):
    function, params = node.items()[0]
    if self.isnoupdate(function) and self.mode != 'init':
        return
    model = self.get_model(function.model)
    if function.eval:
        args = self.process_eval(function.eval)
    else:
        args = self._eval_params(function.model, params)
    uid = self._get_uid(function)  # Added by Smile
    method = function.name
    getattr(model, method)(self.cr, uid, *args)


def new_process_python(self, node):
    def log(msg, *args):
        _logger.log(logging.TEST, msg, *args)
    python, statements = node.items()[0]
    model = self.get_model(python.model)
    statements = statements.replace("\r\n", "\n")
    uid = self._get_uid(python)  # Added by Smile
    create_external_id = lambda name, res_model, res_id: self.pool.get('ir.model.data').create(self.cr, uid, {
        'name': name, 'model': res_model, 'res_id': res_id, 'module': '__test__',
    }, self.context)
    code_context = {'model': model, 'cr': self.cr, 'uid': uid, 'log': log, 'context': self.context,
                    'create_external_id': create_external_id, 'create_xml_id': create_external_id}  # Added by Smile
    code_context.update({'self': model, 'time': time, 'netsvc': netsvc})  # remove me when no !python block test uses 'self' anymore
    try:
        code_obj = compile(statements, self.filename, 'exec')
        unsafe_eval(code_obj, {'ref': self.get_id}, code_context)
    except AssertionError, e:
        self._log_assert_failure(python.severity, 'AssertionError in Python code %s: %s', python.name, e)
        return
    except Exception, e:
        _logger.debug('Exception during evaluation of !python block in yaml_file %s.', self.filename, exc_info=True)
        raise
    else:
        self.assert_report.record(True, python.severity)


def new_process_record(self, node):
    record, fields = node.items()[0]
    model = self.get_model(record.model)
    view_id = record.view
    if view_id and (view_id is not True):
        view_id = self.pool.get('ir.model.data').get_object_reference(self.cr, SUPERUSER_ID, self.module, record.view)[1]
    if model.is_transient():
        record_dict = self.create_osv_memory_record(record, fields)
    else:
        self.validate_xml_id(record.id)
        try:
            self.pool.get('ir.model.data')._get_id(self.cr, SUPERUSER_ID, self.module, record.id)
            default = False
        except ValueError:
            default = True
        uid = self._get_uid(record)  # Added by Smile
        if self.isnoupdate(record) and self.mode != 'init':

            id = self.pool.get('ir.model.data')._update_dummy(self.cr, uid, record.model, self.module, record.id)
            # check if the resource already existed at the last update
            if id:
                self.id_map[record] = int(id)
                return None
            else:
                if not self._coerce_bool(record.forcecreate):
                    return None
        #context = self.get_context(record, self.eval_context)
        #TOFIX: record.context like {'withoutemployee':True} should pass from self.eval_context. example: test_project.yml in project module
        context = record.context
        if view_id:
            varg = view_id
            if view_id is True:
                varg = False
            view = model.fields_view_get(self.cr, SUPERUSER_ID, varg, 'form', context)
            view_id = etree.fromstring(view['arch'].encode('utf-8'))

        record_dict = self._create_record(model, fields, view_id, default=default)
        _logger.debug("RECORD_DICT %s" % record_dict)
        id = self.pool.get('ir.model.data')._update(self.cr, uid, record.model,
                                                    self.module, record_dict, record.id,
                                                    noupdate=self.isnoupdate(record),
                                                    mode=self.mode, context=context)
        self.id_map[record.id] = int(id)
        if config.get('import_partial'):
            self.cr.commit()


def new_process_workflow(self, node):
    workflow, values = node.items()[0]
    if self.isnoupdate(workflow) and self.mode != 'init':
        return
    if workflow.ref:
        id = self.get_id(workflow.ref)
    else:
        if not values:
            raise YamlImportException('You must define a child node if you do not give a ref.')
        if not len(values) == 1:
            raise YamlImportException('Only one child node is accepted (%d given).' % len(values))
        value = values[0]
        if not 'model' in value and (not 'eval' in value or not 'search' in value):
            raise YamlImportException('You must provide a "model" and an "eval" or "search" to evaluate.')
        value_model = self.get_model(value['model'])
        local_context = {'obj': lambda x: value_model.browse(self.cr, self.uid, x, context=self.context)}
        local_context.update(self.id_map)
        id = eval(value['eval'], self.eval_context, local_context)
    uid = self._get_uid(workflow)  # Added by Smile
    self.cr.execute('select distinct signal from wkf_transition')
    signals = [x['signal'] for x in self.cr.dictfetchall()]
    if workflow.action not in signals:
        raise YamlImportException('Incorrect action %s. No such action defined' % workflow.action)
    import openerp.netsvc as netsvc
    wf_service = netsvc.LocalService("workflow")
    wf_service.trg_validate(uid, workflow.model, id, workflow.action, self.cr)

YamlInterpreter.__init__ = new_init
YamlInterpreter._eval_field = _eval_field
YamlInterpreter._get_uid = _get_uid
YamlInterpreter._process_node = new_process_node
YamlInterpreter.process_function = new_process_function
YamlInterpreter.process_python = new_process_python
YamlInterpreter.process_record = new_process_record
YamlInterpreter.process_workflow = new_process_workflow
