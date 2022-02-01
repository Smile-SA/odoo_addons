# -*- coding: utf-8 -*-
# (C) 2022 Smile (<https://www.smile.eu>)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).s

import json
import warnings

from datetime import datetime, date
from functools import wraps

from odoo import models, _
from odoo.http import request, Response
from odoo.tools.safe_eval import safe_eval
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT as DATETIME_FORMAT
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT as DATE_FORMAT


HEADERS = [
    ('Content-Type', 'application/json')
]


def make_error(code, error, description, status, version=False,
               request_data=False):
    response_data = json.dumps({
        'code': code,
        'error': error,
        'description': description,
    })
    if version and version.active_log:
        request.env['api.rest.log'].create_log(
            version.id, request_data, response_data)
    return Response(response_data, status=status, headers=HEADERS)


class RecordNotFoundError(Exception):
    def __init__(self, message):
        """
        :param message: exception message and frontend modal content
        """
        super().__init__(message)

    @property
    def name(self):
        warnings.warn(
            "UserError attribute 'name' is a deprecated alias to args[0]",
            DeprecationWarning)
        return self.args[0]


class api_management():
    def __call__(self, func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            request_data = kwargs
            # Check x-api-key
            _api_key = request.httprequest.headers.get('x-api-key')
            if not _api_key:
                return make_error(
                    1001, 'Unauthorized', _('Unauthenticated user'),
                    status=401)
            # Check api
            _api_version = kwargs.get('_api_version')
            _api_name = kwargs.get('_api_name')
            _api_method = kwargs.get('_api_method')
            if not _api_version and not _api_name:
                return make_error(
                    1002, 'Not found',
                    _('Resource not found or unavailable'), status=404)
            domain_path = [
                ('version_id.name', '=', _api_version),
                ('name', '=', _api_name),
            ]
            http_method = request.httprequest.method.lower()
            if _api_method and _api_method == 'custom':
                http_method = 'custom'
            domain_path += [('method', '=', http_method)]
            path = request.env['api.rest.path'].sudo().search(
                domain_path, limit=1)
            if not path:
                return make_error(
                    1003, 'Not found',
                    _('Resource not found or unavailable'), status=404)
            version = path.version_id
            # Check security
            user = \
                request.env['res.users'].sudo().get_api_rest_user(_api_key)
            if not user or user and user not in version.user_ids:
                return make_error(
                    1004, 'Forbidden', _('Unauthorized access'),
                    status=403, version=version, request_data=request_data)
            kwargs['_api_path'] = path
            try:
                result = decode_bytes(func(*args, **kwargs))
                response_data = json.dumps(result)
                # Create log
                if version.active_log:
                    request.env['api.rest.log'].create_log(
                        version.id, request_data, response_data, user=user)
                request.env.cr.commit()
                return Response(response_data, headers=HEADERS)
            except Exception as e:
                request.env.cr.rollback()
                code = 1005
                status = 500
                error = 'Internal server error'
                description = str(e)
                if isinstance(e, RecordNotFoundError):
                    code = 1006
                    status = 404
                    error = 'Not found'
                response_data = json.dumps({
                    'code': code,
                    'error': error,
                    'description': description,
                })
                # Create log
                if version.active_log:
                    request.env['api.rest.log'].create_log(
                        version.id, request_data, response_data, user=user)
                # Force new commit to save log
                request.env.cr.commit()
                return Response(response_data, status=status, headers=HEADERS)
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
    if isinstance(result, datetime):
        return result.strftime(DATETIME_FORMAT)
    if isinstance(result, date):
        return result.strftime(DATE_FORMAT)
    if isinstance(result, models.BaseModel):
        return result.id
    return result
