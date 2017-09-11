# -*- coding: utf-8 -*-

from functools import wraps
import json

from odoo.http import request


class make_response():

    def __call__(self, func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            result = func(*args, **kwargs)
            return request.make_response(json.dumps(result))
        return wrapper
