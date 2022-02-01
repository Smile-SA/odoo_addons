# -*- coding: utf-8 -*-
# (C) 2022 Smile (<https://www.smile.eu>)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

import json

from odoo import _
from odoo.http import Controller, request, route
from ..tools import api_management, eval_request_params, RecordNotFoundError


def _get_model_obj(model, kwargs):
    user = request.env['res.users'].sudo().get_api_rest_user(
        request.httprequest.headers.get('x-api-key'))
    model_obj = request.env[model].with_user(user)
    # Used *in* of check kwargs to force remove
    # context when value {} is sending
    if 'context' in kwargs:
        model_obj = model_obj.with_context(
            **kwargs.get('context'))
        del kwargs['context']
    return model_obj


class RestApiDocs(Controller):
    @route("/api-docs/v<string:version>", auth="public", methods=["GET"])
    def api_docs(self, version=False, **kwargs):
        domain = [('name', '=', version)]
        version = request.env['api.rest.version'].search(domain, limit=1)
        if not version:
            return request.not_found()
        return request.render("smile_api_rest.openapi", {
            'url_swagger': version.url_swagger
        })

    @route("/api-docs/v<string:version>/swagger.json", auth="public",
           methods=["GET"])
    def api_json(self, version, **kwargs):
        domain = []
        if version:
            domain = [('name', '=', version)]
        version = request.env['api.rest.version'].search(domain, limit=1)
        if not version:
            return {'error': 'API Not found'}
        data = version.get_swagger_json()
        return request.make_response(json.dumps(data), headers=[
            ('Content-Type', 'application/json')
        ])


class RestApi(Controller):
    @route('/api/v<string:_api_version>/<string:_api_name>', auth='public',
           methods=["GET"], csrf=False)
    @api_management()
    def search_read(self, _api_version, _api_name, _api_path, **kwargs):
        eval_request_params(kwargs)
        _api_path._search_treatment_kwargs(kwargs)
        model_obj = _get_model_obj(_api_path.model, kwargs)
        return {
            'results': model_obj.search_read(**kwargs),
            'total': model_obj.search_count(kwargs.get('domain', [])),
            'offset': kwargs.get('offset', 0),
            'limit': kwargs.get('limit', 0),
            'version': _api_version,
        }

    @route('/api/v<string:_api_version>/<string:_api_name>/<int:_api_id>',
           auth='public', methods=["GET"], csrf=False)
    @api_management()
    def read(self, _api_version, _api_name, _api_id, _api_path, **kwargs):
        eval_request_params(kwargs)
        _api_path._read_treatment_kwargs(kwargs)
        model_obj = _get_model_obj(_api_path.model, kwargs)
        read_domain = _api_path._eval_domain(_api_path.filter_domain)
        read_domain += [('id', '=', _api_id)]
        record = model_obj.search(read_domain, limit=1)
        if not record:
            raise RecordNotFoundError(_('Record not found'))
        result = record.read(**kwargs)
        return result and result[0] or {}

    @route('/api/v<string:_api_version>/<string:_api_name>', auth='public',
           methods=["POST"], type='http', csrf=False)
    @api_management()
    def create(self, _api_version, _api_name, _api_path, **kwargs):
        eval_request_params(kwargs)
        model_obj = _get_model_obj(_api_path.model, kwargs)
        return model_obj.create(_api_path._post_treatment_values(kwargs)).id

    @route('/api/v<string:_api_version>/<string:_api_name>/<int:_api_id>',
           auth='public', methods=["PUT"], csrf=False)
    @api_management()
    def write(self, _api_version, _api_name, _api_id, _api_path, **kwargs):
        eval_request_params(kwargs)
        model_obj = _get_model_obj(_api_path.model, kwargs)
        update_domain = _api_path._eval_domain(_api_path.update_domain)
        update_domain += [('id', '=', _api_id)]
        record = model_obj.search(update_domain, limit=1)
        if not record:
            raise RecordNotFoundError(_('Record not found'))
        return record.write(_api_path._post_treatment_values(kwargs))

    @route('/api/v<string:_api_version>/<string:_api_name>/<int:_api_id>',
           auth='public', methods=["DELETE"], csrf=False)
    @api_management()
    def unlink(self, _api_version, _api_name, _api_id, _api_path, **kwargs):
        eval_request_params(kwargs)
        model_obj = _get_model_obj(_api_path.model, kwargs)
        unlink_domain = _api_path._eval_domain(_api_path.unlink_domain)
        unlink_domain += [('id', '=', _api_id)]
        record = model_obj.search(unlink_domain, limit=1)
        if not record:
            raise RecordNotFoundError(_('Record not found'))
        return record.unlink()

    @route([
        '/api/v<string:_api_version>/<string:_api_name>/<string:_api_method>',
        '/api/v<string:_api_version>/<string:_api_name>/<string:_api_method>/<int:_api_id>'
    ], auth='public', methods=["PUT"], csrf=False)
    @api_management()
    def custom_method(self, _api_version, _api_name, _api_method, _api_path,
                      _api_id=False, **kwargs):
        eval_request_params(kwargs)
        model_obj = _get_model_obj(_api_path.model, kwargs)
        if _api_id and _api_path.function_apply_on_record:
            function_domain = _api_path._eval_domain(_api_path.function_domain)
            function_domain += [('id', '=', _api_id)]
            record = model_obj.search(function_domain, limit=1)
            if not record:
                raise RecordNotFoundError(_('Record not found'))
        else:
            record = model_obj.browse()
        kwargs = _api_path._custom_treatment_values(kwargs)
        return getattr(record, _api_path.function)(**kwargs)
