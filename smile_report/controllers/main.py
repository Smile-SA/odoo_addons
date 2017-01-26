# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2015 Smile (<http://www.smile.fr>).
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

import simplejson
import time
from werkzeug import url_decode
from werkzeug.datastructures import Headers
from werkzeug.test import Client
from werkzeug.wrappers import BaseResponse

from openerp.tools import html_escape
from openerp.tools.safe_eval import safe_eval as eval
from openerp.addons.report.controllers.main import ReportController
from openerp.addons.web.controllers.main import _serialize_exception
from openerp.addons.web.http import route, request


@route(['/report/download'], type='http', auth="user")
def report_download(self, data, token):
    """This function is used by 'qwebactionmanager.js' in order to trigger the download of
    a pdf/controller report.

    :param data: a javascript array JSON.stringified containg report internal url ([0]) and
    type [1]
    :returns: Response with a filetoken cookie and an attachment header
    """
    requestcontent = simplejson.loads(data)
    url, type = requestcontent[0], requestcontent[1]
    try:
        if type == 'qweb-pdf':
            reportname = url.split('/report/pdf/')[1].split('?')[0]

            docids = None
            if '/' in reportname:
                reportname, docids = reportname.split('/')

            if docids:
                # Generic report:
                response = self.report_routes(reportname, docids=docids, converter='pdf')
            else:
                # Particular report:
                data = url_decode(url.split('?')[1]).items()  # decoding the args represented in JSON
                response = self.report_routes(reportname, converter='pdf', **dict(data))

            # Added by Smile
            registry, cr, uid, context = request.registry, request.cr, request.session.uid, request.context
            report = registry['report']._get_report_from_name(cr, uid, reportname)
            if docids:
                docids = [int(i) for i in docids.split(',')]
            if report.attachment and docids and len(docids) == 1:
                object = registry[report.model].browse(cr, uid, docids, context)
                filename = eval(report.attachment, {'object': object, 'time': time})
            else:
                filename = '%s.pdf' % report.name
            response.headers.add('Content-Disposition', 'attachment; filename=%s;' % filename)
            ###
            response.set_cookie('fileToken', token)
            return response
        elif type == 'controller':
            reqheaders = Headers(request.httprequest.headers)
            response = Client(request.httprequest.app, BaseResponse).get(url, headers=reqheaders, follow_redirects=True)
            response.set_cookie('fileToken', token)
            return response
        else:
            return
    except Exception, e:
        se = _serialize_exception(e)
        error = {
            'code': 200,
            'message': "Odoo Server Error",
            'data': se
        }
        return request.make_response(html_escape(simplejson.dumps(error)))

ReportController.report_download = report_download
