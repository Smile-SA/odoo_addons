# -*- coding: utf-8 -*-

from functools import wraps
import json

from odoo.http import request
from odoo.tools.safe_eval import safe_eval


class make_response():

    def __call__(self, func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            try:
                result = func(*args, **kwargs)
                return request.make_response(json.dumps(result))
            except Exception, e:
                return request.make_response(json.dumps({'error': str(e)}))
        return wrapper


def eval_request_params(kwargs):
    for k, v in kwargs.iteritems():
        try:
            kwargs[k] = safe_eval(v)
        except:
            continue
