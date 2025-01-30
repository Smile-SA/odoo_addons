# -*- coding: utf-8 -*-
# (C) 2019 Smile (<http://www.smile.eu>)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

import base64
import logging

from odoo import http
from odoo.http import request

from odoo.addons.web.controllers.main import content_disposition

_logger = logging.getLogger(__name__)


class Download(http.Controller):
    """
    Example of utilisation:

    1) Add a "Download" button of type "object" on your form view

    2) Define the method for downloading the file

    from odoo import api, models
    from odoo.tools import ustr


    class StockMove(models.Model):
        _inherit = 'stock.move'

        def _get_datas(self):
            self.ensure_one()
            return ustr("Stock n°%s") % self.id

        def button_get_file(self):
            self.ensure_one()
            return {
                'type': 'ir.actions.act_url',
                'url': '/download/saveas?model=%(model)s&record_id=%(record_id)s&method=%(method)s&filename=%(filename)s' % {
                    'filename': 'stock_infos.txt',
                    'model': self._name,
                    'record_id': self.id,
                    'method': '_get_datas',
                },
                'target': 'self',
            }

    """

    @http.route('/download/saveas', type='http', auth="public")
    def saveas(self, model, record_id, method, encoded=False, filename=None,
               **kw):
        """ Download link for files generated on the fly.

        :param str model: name of the model to fetch the data from
        :param str record_id: id of the record from which to fetch the data
        :param str method: name of the method used to fetch data
        :param bool encoded: whether the data is encoded in base64
        :param str filename: the file's name, if any
        :returns: :class:`werkzeug.wrappers.Response`
        """
        Model = request.env[model]
        record = Model.browse(int(record_id))

        if not hasattr(record, method):
            return request.not_found()

        method_to_call = getattr(record, method)

        try:
            datas = method_to_call()
        except Exception as e:
            _logger.error(e)
            return request.not_found()

        if not datas:
            return request.not_found()

        filecontent = datas[0]
        if not filecontent:
            return request.not_found()

        if encoded:
            filecontent = base64.b64decode(filecontent)

        if not filename:
            filename = '%s_%s' % (model.replace('.', '_'), record_id)

        return request.make_response(
            filecontent, [
                ('Content-Type', 'application/octet-stream'),
                ('Content-Disposition', content_disposition(filename)),
            ])
