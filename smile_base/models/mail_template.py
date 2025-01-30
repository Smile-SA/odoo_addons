# -*- coding: utf-8 -*-
# (C) 2019 Smile (<http://www.smile.eu>)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

import sys

from odoo import api, models, tools, _
from odoo.exceptions import UserError
from odoo.addons.mail.models.mail_render_mixin import \
    format_date, _logger

if sys.version_info > (3,):
    long = int


class MailTemplate(models.Model):
    _inherit = "mail.template"

    def format_numeric(self, value, column, options=None):
        try:
            model, fieldname = column.split(',')
            field = self.env[model]._fields[fieldname]
            converter = self.env['ir.qweb.field.%s' % field.type]
            return converter.value_to_html(value, field, options)
        except Exception:
            return value

    @api.model
    def render_template(self, template_txt, model, res_ids,
                        post_process=False):
        """ Render the given template text, replace mako expressions
        ``${expr}`` with the result of evaluating these expressions
        with an evaluation context containing:

         - ``user``: browse_record of the current user
         - ``object``: record of the document record this mail is related to
         - ``context``: the context passed to the mail composition wizard

        :param str template_txt: the template text to render
        :param str model: model name of the document record
            this mail is related to.
        :param int res_ids: list of ids of document records
            those mails are related to.
        """
        multi_mode = True
        if isinstance(res_ids, (int, long)):
            multi_mode = False
            res_ids = [res_ids]

        results = dict.fromkeys(res_ids, u"")

        # try to load the template
        try:
            mako_env = self._context.get('safe')
            template = mako_env.from_string(tools.ustr(template_txt))
        except Exception:
            _logger.info("Failed to load template %r", template_txt,
                         exc_info=True)
            return multi_mode and results or results[res_ids[0]]

        # prepare template variables
        # filter to avoid browsing [None]
        records = self.env[model].browse(list(filter(None, res_ids)))
        res_to_rec = dict.fromkeys(res_ids, None)
        for record in records:
            res_to_rec[record.id] = record
        variables = {
            'format_date': lambda date, format=False, context=self._context:
                format_date(self.env, date, format),
            'format_datetime': lambda dt, tz=False, format=False,
                context=self._context:
                tools.format_datetime(self.env, dt, tz, format),
            'format_amount': lambda amount, currency, context=self._context:
                tools.format_amount(self.env, amount, currency),
            'format_numeric': lambda value, column, options=None:
                self.format_numeric(value, column, options),  # Added by Smile
            'user': self.env.user,
            'ctx': self._context,  # context kw would clash with mako internals
        }
        for res_id, record in res_to_rec.items():
            variables['object'] = record
            try:
                render_result = template.render(variables)
            except Exception:
                _logger.info("Failed to render template %r using values %r"
                             % (template, variables), exc_info=True)
                raise UserError(
                    _("Failed to render template %r using values %r")
                    % (template, variables))
            if render_result == u"False":
                render_result = u""
            results[res_id] = render_result

        if post_process:
            for res_id, result in results.items():
                results[res_id] = self.render_post_process(result)

        return multi_mode and results or results[res_ids[0]]
