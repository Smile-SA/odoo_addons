# -*- coding: utf-8 -*-

from datetime import datetime
from dateutil.relativedelta import relativedelta
from operator import and_, or_, sub
import time

from openerp import api, _
from openerp.models import BaseModel
from openerp.osv.expression import normalize_domain

SET_OPERATORS = {
    '&': and_,
    '|': or_,
    '!': sub,
}
SQL2PYTHON_OPERATORS = {
    '=': '==',
    '<>': '!=',
    'like': 'in',
    'ilike': 'in',
    'not like': 'not in',
    'not ilike': 'not in',
}


@api.multi
def filtered_from_domain(self, domain):
    if not domain or not self:
        return self

    def get_records(item):
        records = self
        remote_field = item[0].split('.')[:-1]
        if remote_field:
            records = eval("rec.mapped('%s')" % '.'.join(remote_field), {'rec': self})
        return records

    def get_field(item):
        return get_records(item)._fields[item[0].split('.')[-1]]

    def extend(domain):
        for index, item in enumerate(domain):
            if isinstance(item, list):
                field = get_field(item)
                if field.search and not field.related:
                    extension = field.search(get_records(item), *item[1:])
                    domain = domain[:index] + normalize_domain(extension) + domain[index + 1:]
        return domain

    localdict = {'time': time, 'datetime': datetime, 'relativedelta': relativedelta,
                 'context': self._context, 'uid': self._uid, 'user': self.env.user}
    try:
        if not isinstance(domain, basestring):
            domain = repr(domain)
        domain = extend(normalize_domain(eval(domain, localdict)))
    except:
        raise Warning(_('Domain not supported for %s filtering: %s') % (self._name, domain))

    stack = []

    def preformat(item):
        if isinstance(item, tuple):
            item = list(item)
        reverse = False
        field = get_field(item)
        if field.relational:
            if isinstance(item[2], basestring):
                item[2] = dict(self.env[field.comodel_name].name_search(name=item[2], operator=item[1], limit=0)).keys()
                item[1] = 'in'
            item[0] = 'rec.%s' % item[0]
            if field.type.endswith('2many'):
                item[0] += '.ids'
                py_operator = SQL2PYTHON_OPERATORS.get(item[1], item[1])
                if py_operator in ('in', 'not in'):
                    item[0] = '%sset(%s)' % (py_operator.startswith('not') and 'not ' or '', item[0])
                    item[1] = '&'
                    item[2] = set(item[2])
            else:
                item[0] += '.id'
        else:
            reverse = 'like' in item[1]
            item[0] = 'rec.%s' % item[0]
        item[1] = SQL2PYTHON_OPERATORS.get(item[1], item[1])
        item[2] = repr(item[2])
        if reverse:
            item = item[::-1]
        return ' '.join(map(str, item))

    def compute(item):
        try:
            expr = preformat(item)
            return self.filtered(lambda rec: eval(expr, dict(localdict, rec=rec)))
        except:
            return self.browse()

    def parse():
        for item in domain[::-1]:
            if isinstance(item, (tuple, list)):
                stack.append(compute(item))
            else:
                a = stack.pop()
                if item == '!':
                    b = self
                else:
                    b = stack.pop()
                stack.append(SET_OPERATORS[item](b, a))
        return stack.pop()

    return parse()

BaseModel.filtered_from_domain = filtered_from_domain
