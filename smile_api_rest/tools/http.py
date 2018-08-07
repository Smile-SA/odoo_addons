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
                result = decode_bytes(func(*args, **kwargs))
                return request.make_response(json.dumps(result))
            except Exception as e:
                return request.make_response(json.dumps({'error': str(e)}))
        return wrapper


def eval_request_params(kwargs):
    for k, v in kwargs.items():
        try:
            kwargs[k] = safe_eval(v)
        except Exception:
            continue


def decode_bytes(result):
    if isinstance(result, (list, tuple)):
        decoded_result = []
        for item in result:
            decoded_result.append(decode_bytes(item))
        return decoded_result
    if isinstance(result, dict):
        decoded_result = {}
        for k, v in result.items():
            decoded_result[decode_bytes(k)] = decode_bytes(v)
        return decoded_result
    if isinstance(result, bytes):
        return result.decode('utf-8')
    return result
