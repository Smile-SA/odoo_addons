# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2011-2012 Casden (<http://www.casden.fr>).
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

from report import report_sxw


class ReportWebkitHtmlModelReport(report_sxw.rml_parse):

    def __init__(self, cr, uid, name, context):
        super(ReportWebkitHtmlModelReport, self).__init__(cr, uid, name, context=context)
        self.localcontext.update({
            'pool': self.pool,
            'cr': cr,
            'uid': uid,
            'lang': self.pool.get('res.users').browse(cr, uid, uid, context).context_lang,
            'translate': lambda cr, uid, obj, field, type, lang, src=None: obj.pool.get('ir.translation')._get_source(cr, uid,
                                                                                                                      '%s,%s' % (obj._name, field),
                                                                                                                      type, lang, src),
        })


report_sxw.report_sxw('report.webkitmodel.report',
                      'ir.model',
                      'smile-addons/smile_model_report/report/report_webkit_html_model_report.mako',
                      parser=ReportWebkitHtmlModelReport)
